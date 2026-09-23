from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import subprocess
import tempfile
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
import base64
from fastapi.responses import StreamingResponse
import re
import json

app = FastAPI(title="PySHS Web Interface", version="3.2.2")

# Dossier de travail (même logique que le manuel)
WORK_DIR = Path("Work")
WORK_DIR.mkdir(exist_ok=True)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")


# ------------------------------------------------------------
# Modèles de données
# ------------------------------------------------------------

class HRSRequest(BaseModel):
    keyword: str
    beta_content: str
    theta: float = 90.0          # angle de diffusion en degrés

class SHSRequest(BaseModel):
    keyword: str
    beta_content: str
    orientation_content: str
    n_dipoles: int = 24
    wavelength: float = 800.0
    n_real: float = 1.33
    n_imag: float = 0.0
    theta: float = 90.0
    n_points: int = 20



class SphereRequest(BaseModel):
    keyword: str
    beta_content: str
    n_index: float = 1.33
    wavelength: float = 800.0
    radius: float = 50.0            # nm


# ------------------------------------------------------------
# Fonction utilitaire : écriture temporaire + exécution
# ------------------------------------------------------------

def run_binary(binary_name: str, args: list, timeout: int = 120) -> dict:
    """Exécute un binaire PySHS et retourne stdout + stderr"""
    binary_path = WORK_DIR / binary_name

    if not binary_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Binaire {binary_name} introuvable dans {WORK_DIR.resolve()}. "
                   f"Vérifiez qu'il est bien présent et exécutable."
        )

    # Important : on passe seulement le nom du binaire car cwd = WORK_DIR
    cmd = [f"./{binary_name}"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORK_DIR)          # on se place dans Work/
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Calcul trop long (timeout)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        
# ---------------------------------------------------------------        
# fonction plots
# ---------------------------------------------------------------        
        
def generate_plots(keyword: str, job_id: str, orient_file: Path = None) -> dict:
    """Génère les graphiques (PNG + PDF) et retourne les chemins"""
    plots = {}
    out_plot = WORK_DIR / "out_plot"
    static_dir = Path("static/plots")
    static_dir.mkdir(parents=True, exist_ok=True)

    try:
        if keyword.startswith("polarplot"):
            img_png = static_dir / f"polar_{job_id}.png"
            img_pdf = static_dir / f"polar_{job_id}.pdf"
            subprocess.run(
                ["python3", "Src/graph_polar.py", str(out_plot), str(img_png)],
                check=True, capture_output=True, text=True
            )
            # On génère aussi le PDF
            subprocess.run(
                ["python3", "Src/graph_polar.py", str(out_plot), str(img_pdf)],
                check=True, capture_output=True, text=True
            )
            plots["polar"] = {
                "png": f"/static/plots/polar_{job_id}.png",
                "pdf": f"/static/plots/polar_{job_id}.pdf"
            }

        elif keyword == "angle_scattering":
            img_png = static_dir / f"angle_{job_id}.png"
            img_pdf = static_dir / f"angle_{job_id}.pdf"
            subprocess.run(
                ["python3", "Src/graph_angle.py", str(out_plot), str(img_png)],
                check=True, capture_output=True, text=True
            )
            subprocess.run(
                ["python3", "Src/graph_angle.py", str(out_plot), str(img_pdf)],
                check=True, capture_output=True, text=True
            )
            plots["angle"] = {
                "png": f"/static/plots/angle_{job_id}.png",
                "pdf": f"/static/plots/angle_{job_id}.pdf"
            }

        # Graphique d'assemblage
        if orient_file and orient_file.exists():
            img_png = static_dir / f"assembly_{job_id}.png"
            img_pdf = static_dir / f"assembly_{job_id}.pdf"
            subprocess.run(
                ["python3", "Src/graph_assembly.py", str(orient_file), str(img_png)],
                check=True, capture_output=True, text=True
            )
            subprocess.run(
                ["python3", "Src/graph_assembly.py", str(orient_file), str(img_pdf)],
                check=True, capture_output=True, text=True
            )
            plots["assembly"] = {
                "png": f"/static/plots/assembly_{job_id}.png",
                "pdf": f"/static/plots/assembly_{job_id}.pdf"
            }

    except Exception as e:
        plots["error"] = str(e)

    return plots      
        
        
# ------------------------------------------------------------
# Endpoint HRS
# ------------------------------------------------------------

from fastapi.responses import StreamingResponse
import re
import json


@app.post("/api/save_result")
async def save_result(content: str = Form(...), filename: str = Form("resultat_pyshs.txt")):
    """Permet de télécharger le texte de résultat"""
    temp_file = WORK_DIR / filename
    temp_file.write_text(content)
    return FileResponse(
        path=temp_file,
        filename=filename,
        media_type="text/plain"
    )






@app.post("/api/shs_stream")
async def run_shs_stream(req: SHSRequest):
    job_id = str(uuid.uuid4())[:8]
    beta_file = WORK_DIR / f"beta_{job_id}.txt"
    orient_file = WORK_DIR / f"orient_{job_id}.txt"
    output_file = WORK_DIR / f"out_shs_{job_id}.txt"

    with open(beta_file, "w") as f:
        f.write(req.beta_content)
    with open(orient_file, "w") as f:
        f.write(req.orientation_content)

    args = [req.keyword, beta_file.name, orient_file.name, output_file.name]
    input_data = (
        f"{req.n_dipoles}\n"
        f"{req.wavelength}\n"
        f"{req.n_real}\n"
        f"{req.n_imag}\n"
        f"{req.theta}\n"
    )
    # Si c'est angle_scattering, on ajoute le nombre de points
    if req.keyword == "angle_scattering":
        input_data += f"{req.n_points}\n"

    def event_generator():
        try:
            # stdbuf -oL force le programme C à écrire ligne par ligne
            process = subprocess.Popen(
                ["./SHS"] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(WORK_DIR),
                bufsize=1
            )

            process.stdin.write(input_data)
            process.stdin.flush()
            process.stdin.close()

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Détection du pourcentage (plus souple)
                match = re.search(r'([\d.]+)\s*pourcent', line, re.IGNORECASE)
                if match:
                    percent = min(100.0, float(match.group(1)))
                    yield f"data: {json.dumps({'type': 'progress', 'percent': percent})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'log', 'message': line})}\n\n"

            process.wait()

            content = ""
            if output_file.exists():
                content = output_file.read_text()

            plots = generate_plots(req.keyword, job_id, orient_file)

            yield f"data: {json.dumps({'type': 'done', 'success': process.returncode == 0, 'result': content, 'plots': plots, 'job_id': job_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            beta_file.unlink(missing_ok=True)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/hrs")
async def run_hrs(req: HRSRequest):
    job_id = str(uuid.uuid4())[:8]
    beta_file = WORK_DIR / f"beta_{job_id}.txt"
    output_file = WORK_DIR / f"out_hrs_{job_id}.txt"

    with open(beta_file, "w") as f:
        f.write(req.beta_content)

    try:
        args = [req.keyword, beta_file.name, output_file.name]
        input_data = f"{req.theta}\n"

        result = subprocess.run(
            ["./HRS"] + args,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(WORK_DIR)
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur HRS (code {result.returncode}) :\n"
                       f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        content = output_file.read_text() if output_file.exists() else result.stdout

        # ---------- Génération des graphiques ----------
        plots = generate_plots(req.keyword, job_id, orient_file=None)

        return {
            "success": True,
            "job_id": job_id,
            "stdout": result.stdout,
            "result": content,
            "plots": plots
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Timeout – calcul HRS trop long")
    finally:
        beta_file.unlink(missing_ok=True)


# ------------------------------------------------------------
# Endpoint SHS (structures supramoléculaires)
# ------------------------------------------------------------



@app.post("/api/generate_sphere")
async def generate_sphere(
    radius: float = 50.0,
    n_dipoles: int = 100,
    sigma: float = 0.3
):
    job_id = str(uuid.uuid4())[:8]
    orient_file = WORK_DIR / f"orient_sphere_{job_id}.txt"

    try:
        result = subprocess.run(
            [
                "python3", "Src/script_sphere_random.py",
                str(orient_file),
                str(radius),
                str(n_dipoles),
                str(sigma)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur génération sphère :\n{result.stderr}\n{result.stdout}"
            )

        content = orient_file.read_text()

        return {
            "success": True,
            "content": content,
            "message": f"Sphère générée ({n_dipoles} dipôles, rayon={radius} nm, σ={sigma})"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------
# Endpoint Sphere / Cylinder
# ------------------------------------------------------------

@app.post("/api/sphere")
async def run_sphere(req: SphereRequest):
    job_id = str(uuid.uuid4())[:8]
    beta_file = WORK_DIR / f"beta_{job_id}.txt"
    output_file = WORK_DIR / f"out_sphere_{job_id}.txt"

    with open(beta_file, "w") as f:
        f.write(req.beta_content)

    try:
        args = [req.keyword, beta_file.name, output_file.name]
        result = run_binary("sphere_SHS", args)

        if result["returncode"] != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur sphere_SHS :\n{result['stderr']}\n{result['stdout']}"
            )

        content = output_file.read_text() if output_file.exists() else ""
        return {
            "success": True,
            "job_id": job_id,
            "stdout": result["stdout"],
            "result": content
        }
    finally:
        beta_file.unlink(missing_ok=True)


# ------------------------------------------------------------
# Téléchargement d’un fichier de résultat
# ------------------------------------------------------------

@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    # Cherche le premier fichier qui correspond
    for f in WORK_DIR.glob(f"out_*_{job_id}.txt"):
        return FileResponse(f, filename=f.name)
    raise HTTPException(status_code=404, detail="Fichier introuvable")


# ------------------------------------------------------------
# Exemple de fichier beta (pour aider l’utilisateur)
# ------------------------------------------------------------

@app.get("/api/example/beta")
async def example_beta():
    example = """# Example hyperpolarizability tensor (a.u.)
xxx 0.0
xxy 0.0
xxz 0.0
xyx 0.0
xyy 0.0
xyz 0.0
xzx 0.0
xzy 0.0
xzz 0.0
yxx 0.0
yxy 0.0
yxz 0.0
yyx 0.0
yyy 0.0
yyz 0.0
yzx 0.0
yzy 0.0
yzz 0.0
zxx 0.0
zxy 0.0
zxz 0.0
zyx 0.0
zyy 0.0
zyz 0.0
zzx 0.0
zzy 0.0
zzz 1.0
"""
    return {"content": example}
