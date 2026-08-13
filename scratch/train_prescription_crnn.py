"""
train_prescription_crnn.py  v2
──────────────────────────────
Train the Doctor's Prescription BD Dataset 78-class CRNN medicine classifier.
Uses PyTorch with synthetic handwriting-style rendered images.

Architecture (exact Kaggle notebook port):
  Input(3, 32, 128)
  → Conv2D(32)+BN+ReLU → MaxPool  →  (32,16,64)
  → Conv2D(64)+BN+ReLU → MaxPool  →  (64, 8,32)
  → Conv2D(128)+BN+ReLU → MaxPool → (128, 4,16)
  → Flatten(8192)
  → Dense(1024)+ReLU+Dropout(0.55)
  → Dense(78)  [Softmax @ inference]

Saves:
  backend/models/prescription_crnn.pt
  backend/models/prescription_classes.json
"""

import os, sys, time, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, accuracy_score, top_k_accuracy_score
)

# ─── Config ─────────────────────────────────────────────────────────────────────
IMG_W, IMG_H = 128, 32
SAMPLES_PER_CLASS   = 100        # 100 × 107 = 10,700 total
BATCH_SIZE          = 128
LR                  = 0.0008
EPOCHS              = 20
EARLY_STOP_PATIENCE = 4
DROPOUT             = 0.40
MODEL_OUT  = os.path.join("backend", "models", "prescription_crnn.pt")
CLASS_OUT  = os.path.join("backend", "models", "prescription_classes.json")
os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)

# ─── 78-Class BD Vocabulary ──────────────────────────────────────────────────────
MEDICINE_DB = {
    "Aceta":"Paracetamol","Aciclover":"Acyclovir","Aclomed":"Acyclovir",
    "Activ":"Multivitamin","Aeron":"Levocetirizine","Agimox":"Amoxicillin",
    "Alaspan":"Loratadine","Algin":"Algeldrate + Magnesium Hydroxide",
    "Almex":"Albendazole","Amdocal":"Amlodipine","Amide":"Amitriptyline",
    "Amipace":"Amoxicillin","Amolex":"Amoxicillin","Amope":"Amoxicillin + Cloxacillin",
    "Amoxil":"Amoxicillin","Amoxipen":"Amoxicillin","Ampicil":"Ampicillin",
    "Ampimax":"Ampicillin","Apsin":"Erythromycin","Aran":"Rabeprazole",
    "Arlin":"Metronidazole","Arviox":"Azithromycin","Asicam":"Piroxicam",
    "Asmol":"Salbutamol","Atarax":"Hydroxyzine","Atrocid":"Atropine",
    "Avilin":"Chlorphenamine","Azilide":"Azithromycin","Azipen":"Azithromycin",
    "Azit":"Azithromycin","Azifast":"Azithromycin","Azimax":"Azithromycin",
    "Azithral":"Azithromycin","Azitop":"Azithromycin","Cefim":"Cefixime",
    "Cefimax":"Cefixime","Cefix":"Cefixime","Cefolac":"Cefuroxime",
    "Ciproflox":"Ciprofloxacin","Ciprocin":"Ciprofloxacin",
    "Clavam":"Amoxicillin + Clavulanate","Clenol":"Clonazepam",
    "Clofix":"Cloxacillin","Coamoxil":"Amoxicillin + Clavulanate",
    "Cosamox":"Co-trimoxazole","Dexacin":"Dexamethasone",
    "Diclofen":"Diclofenac","Diclogesic":"Diclofenac",
    "Doclav":"Amoxicillin + Clavulanate","Domni":"Domperidone",
    "Donasma":"Theophylline","Doxilen":"Doxycycline","Duricef":"Cefadroxil",
    "Emox":"Amoxicillin","Enalapril":"Enalapril","Erythrocin":"Erythromycin",
    "Esomep":"Esomeprazole","Ethatab":"Ethambutol","Famox":"Famotidine",
    "Fenadin":"Fexofenadine","Filmet":"Metronidazole","Fixim":"Cefixime",
    "Flamar":"Diclofenac","Flixol":"Fluconazole","Gaviscon":"Alginate + Antacid",
    "Gentacin":"Gentamicin","Glex":"Glibenclamide","Hyper":"Captopril",
    "Inac":"Indomethacin","Iprolam":"Alprazolam","Keflex":"Cefalexin",
    "Kenacort":"Triamcinolone","Ketocon":"Ketoconazole","Loperamide":"Loperamide",
    "Maxpro":"Esomeprazole","Metronid":"Metronidazole","Moxacil":"Amoxicillin",
    "Napa":"Paracetamol","Napadol":"Paracetamol","Neomox":"Amoxicillin",
    "Neoceptin":"Ranitidine","Neoflam":"Naproxen","Neomet":"Metformin",
    "Novamet":"Metformin","Omidon":"Domperidone","Omifast":"Omeprazole",
    "Omeprazol":"Omeprazole","Omep":"Omeprazole","Pantonix":"Pantoprazole",
    "Partamol":"Paracetamol","Raniclor":"Ranitidine","Ranitid":"Ranitidine",
    "Seclo":"Esomeprazole","Sertralin":"Sertraline","Sineflex":"Chlorpromazine",
    "Sulphamet":"Sulfamethoxazole","Synasma":"Theophylline","Tetrabon":"Tetracycline",
    "Torizid":"Tramadol","Trimox":"Amoxicillin","Viogesic":"Naproxen",
    "Zantac":"Ranitidine","Zerocid":"Omeprazole","Zinacef":"Cefuroxime",
    "Zirocin":"Azithromycin","Zithro":"Azithromycin","Zithromax":"Azithromycin"
}
CLASSES      = sorted(MEDICINE_DB.keys())
CLS2IDX      = {c: i for i, c in enumerate(CLASSES)}
IDX2CLS      = {i: c for c, i in CLS2IDX.items()}
NUM_CLS      = len(CLASSES)
print(f"[INFO] {NUM_CLS} classes · {SAMPLES_PER_CLASS} samples each = {NUM_CLS*SAMPLES_PER_CLASS:,} images")

# ─── Fonts ──────────────────────────────────────────────────────────────────────
FONT_PATHS = [
    "C:/Windows/Fonts/KUNSTLER.TTF",
    "C:/Windows/Fonts/FREESCPT.TTF",
    "C:/Windows/Fonts/comic.ttf",
    "C:/Windows/Fonts/Arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/verdana.ttf",
]
AVAILABLE_FONTS = [f for f in FONT_PATHS if os.path.exists(f)]
print(f"[INFO] Available fonts: {[os.path.basename(f) for f in AVAILABLE_FONTS]}")


# ─── Image Generator ─────────────────────────────────────────────────────────────
def make_image(text: str, augment: bool = True) -> np.ndarray:
    """
    Render a 32×128 px RGB handwriting-style word image.
    Returns float32 array in [0,1] shape (H,W,3).
    """
    W, H = IMG_W, IMG_H
    bg = tuple(random.randint(230, 255) for _ in range(3)) if augment else (248, 248, 248)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    ink = tuple(random.randint(0, 50) for _ in range(3)) if augment else (15, 15, 25)
    sz  = random.randint(11, 17) if augment else 14

    fp  = random.choice(AVAILABLE_FONTS) if AVAILABLE_FONTS else None
    try:
        font = ImageFont.truetype(fp, sz) if fp else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    try:
        bb = draw.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    except AttributeError:
        tw, th = font.getsize(text)

    dx = random.randint(-5, 5) if augment else 0
    dy = random.randint(-3, 3) if augment else 0
    x  = max(1, (W - tw) // 2 + dx)
    y  = max(1, (H - th) // 2 + dy)
    draw.text((x, y), text, fill=ink, font=font)

    if augment:
        angle = random.uniform(-6, 6)
        img   = img.rotate(angle, fillcolor=bg, expand=False)
        if random.random() < 0.4:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.9)))

    arr = np.array(img, dtype=np.float32)

    if augment:
        # brightness/contrast jitter
        arr = np.clip(arr * random.uniform(0.80, 1.20) + random.randint(-15, 15), 0, 255)
        # noise
        if random.random() < 0.40:
            arr = np.clip(arr + np.random.normal(0, random.uniform(1, 7), arr.shape), 0, 255)
        # perspective shear
        if random.random() < 0.25:
            pts1 = np.float32([[0,0],[W,0],[0,H],[W,H]])
            d    = random.randint(-7, 7)
            pts2 = np.float32([[d,0],[W+d,0],[0,H],[W,H]])
            M    = cv2.getPerspectiveTransform(pts1, pts2)
            arr  = cv2.warpPerspective(arr, M, (W, H),
                                       borderMode=cv2.BORDER_CONSTANT,
                                       borderValue=list(bg))

    arr = cv2.resize(arr.astype(np.uint8), (W, H)).astype(np.float32)
    return arr / 255.0


# ─── Build Dataset ───────────────────────────────────────────────────────────────
def build_dataset():
    t = time.time()
    N = NUM_CLS * SAMPLES_PER_CLASS
    X = np.empty((N, IMG_H, IMG_W, 3), dtype=np.float32)
    y = np.empty(N, dtype=np.int64)
    idx = 0
    for cls_name in CLASSES:
        ci = CLS2IDX[cls_name]
        for s in range(SAMPLES_PER_CLASS):
            X[idx] = make_image(cls_name, augment=(s < SAMPLES_PER_CLASS - 15))
            y[idx] = ci
            idx += 1
    print(f"[INFO] Dataset built in {time.time()-t:.1f}s  shape={X.shape}")
    return X, y


# ─── PyTorch Dataset ─────────────────────────────────────────────────────────────
class MedDS(Dataset):
    def __init__(self, X, y):
        self.X = torch.from_numpy(X.transpose(0,3,1,2))  # NHWC→NCHW
        self.y = torch.from_numpy(y)
    def __len__(self):  return len(self.y)
    def __getitem__(self, i): return self.X[i], self.y[i]


# ─── Model (Kaggle notebook architecture, PyTorch) ───────────────────────────────
class PrescriptionCRNN(nn.Module):
    def __init__(self, nc=NUM_CLS, dp=DROPOUT):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: (3,32,128) → (32,16,64)
            nn.Conv2d(3,  32, 3, padding=1), nn.BatchNorm2d(32),  nn.ReLU(True), nn.MaxPool2d(2),
            # Block 2: → (64,8,32)
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64),  nn.ReLU(True), nn.MaxPool2d(2),
            # Block 3: → (128,4,16)
            nn.Conv2d(64,128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(True), nn.MaxPool2d(2),
        )
        flat = 128 * (IMG_H//8) * (IMG_W//8)   # 128 × 4 × 16 = 8192
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat, 1024), nn.ReLU(True), nn.Dropout(dp),
            nn.Linear(1024, nc),
        )
    def forward(self, x): return self.head(self.features(x))


# ─── Train / Eval helpers ────────────────────────────────────────────────────────
def run_epoch(model, loader, opt, crit, device, train=True):
    model.train(train)
    tloss = tcorr = tn = 0
    with torch.set_grad_enabled(train):
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            logits = model(xb)
            loss   = crit(logits, yb)
            if train:
                opt.zero_grad(); loss.backward(); opt.step()
            tloss += loss.item() * len(yb)
            tcorr += (logits.argmax(1)==yb).sum().item()
            tn    += len(yb)
    return tloss/tn, tcorr/tn


@torch.no_grad()
def collect_preds(model, loader, device):
    model.eval()
    all_p, all_g, all_prob = [], [], []
    for xb, yb in loader:
        logits = model(xb.to(device))
        prob   = torch.softmax(logits, 1).cpu().numpy()
        preds  = logits.argmax(1).cpu().numpy()
        all_p.extend(preds); all_g.extend(yb.numpy()); all_prob.append(prob)
    return np.array(all_p), np.array(all_g), np.vstack(all_prob)


# ─── Main ────────────────────────────────────────────────────────────────────────
def main():
    t0  = time.time()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Device: {dev}")
    torch.manual_seed(42); np.random.seed(42); random.seed(42)

    # 1. Build dataset
    X, y = build_dataset()

    # 2. Split 70 / 15 / 15
    Xtmp, Xte, ytmp, yte = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)
    Xtr, Xva, ytr, yva   = train_test_split(Xtmp, ytmp, test_size=0.176, stratify=ytmp, random_state=42)
    print(f"[INFO] Train={len(ytr):,}  Val={len(yva):,}  Test={len(yte):,}")

    trn_dl = DataLoader(MedDS(Xtr, ytr), BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=False)
    val_dl = DataLoader(MedDS(Xva, yva), BATCH_SIZE, shuffle=False, num_workers=0)
    tst_dl = DataLoader(MedDS(Xte, yte), BATCH_SIZE, shuffle=False, num_workers=0)

    # 3. Model + optimiser
    model  = PrescriptionCRNN(NUM_CLS, DROPOUT).to(dev)
    crit   = nn.CrossEntropyLoss(label_smoothing=0.05)
    opt    = optim.Adam(model.parameters(), lr=LR, betas=(0.9,0.999), weight_decay=1e-5)
    sched  = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=2, factor=0.5)

    nparams = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Parameters: {nparams:,}")

    # 4. Training loop
    best_vacc  = 0.0
    best_state = None
    patience   = 0
    history    = []

    hdr = f"{'Ep':>4} {'TrLoss':>8} {'TrAcc':>7} {'VaLoss':>8} {'VaAcc':>7} {'LR':>9}"
    print(f"\n{hdr}\n{'-'*50}")

    for ep in range(1, EPOCHS+1):
        trl, tra = run_epoch(model, trn_dl, opt, crit, dev, train=True)
        val, vaa = run_epoch(model, val_dl, opt, crit, dev, train=False)
        sched.step(val)
        lr = opt.param_groups[0]['lr']
        history.append(dict(epoch=ep, train_acc=tra, val_acc=vaa))

        print(f"{ep:4d} {trl:8.4f} {tra*100:6.2f}% {val:8.4f} {vaa*100:6.2f}% {lr:.6f}")

        if vaa > best_vacc:
            best_vacc  = vaa
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience   = 0
        else:
            patience += 1
            if patience >= EARLY_STOP_PATIENCE:
                print(f"\n[STOP] Early stopping at epoch {ep}")
                break

    print(f"\n[BEST] Val accuracy: {best_vacc*100:.2f}%")

    # 5. Test evaluation
    model.load_state_dict(best_state)
    tst_preds, tst_labels, tst_probs = collect_preds(model, tst_dl, dev)
    test_acc = accuracy_score(tst_labels, tst_preds)
    top5_acc = top_k_accuracy_score(tst_labels, tst_probs, k=5)

    print(f"\n{'='*55}")
    print(f"  FINAL TEST RESULTS")
    print(f"{'='*55}")
    print(f"  Top-1 Accuracy : {test_acc*100:.2f}%")
    print(f"  Top-5 Accuracy : {top5_acc*100:.2f}%")
    print(f"{'='*55}")

    # 6. Per-class report (top 20 by F1)
    cls_names = [IDX2CLS[i] for i in range(NUM_CLS)]
    report    = classification_report(tst_labels, tst_preds, target_names=cls_names,
                                      labels=list(range(NUM_CLS)), output_dict=True)
    per_f1    = {c: report[c]['f1-score'] for c in cls_names if c in report}
    top20     = sorted(per_f1.items(), key=lambda x: x[1], reverse=True)[:20]

    print(f"\n  Top-20 Classes by F1-Score")
    print(f"  {'Brand':<16} {'F1':>7} {'Prec':>7} {'Rec':>7}")
    print(f"  {'-'*42}")
    for brand, f1 in top20:
        p = report[brand]['precision']
        r = report[brand]['recall']
        print(f"  {brand:<16} {f1*100:>6.1f}% {p*100:>6.1f}% {r*100:>6.1f}%")

    mf1 = report['macro avg']['f1-score']
    wf1 = report['weighted avg']['f1-score']
    print(f"\n  Macro Avg F1   : {mf1*100:.2f}%")
    print(f"  Weighted F1    : {wf1*100:.2f}%")

    # 7. Save model
    torch.save({
        "model_state"   : best_state,
        "class_to_idx"  : CLS2IDX,
        "idx_to_class"  : IDX2CLS,
        "medicine_db"   : MEDICINE_DB,
        "num_classes"   : NUM_CLS,
        "img_w"         : IMG_W,
        "img_h"         : IMG_H,
        "test_accuracy" : float(test_acc),
        "val_accuracy"  : float(best_vacc),
        "top5_accuracy" : float(top5_acc),
        "macro_f1"      : float(mf1),
        "history"       : history,
        "dropout"       : DROPOUT,
    }, MODEL_OUT)

    with open(CLASS_OUT, 'w') as f:
        json.dump({
            "classes"     : CLASSES,
            "class_to_idx": CLS2IDX,
            "idx_to_class": {str(k): v for k, v in IDX2CLS.items()},
            "medicine_db" : MEDICINE_DB
        }, f, indent=2)

    print(f"\n[SAVED] {MODEL_OUT}")
    print(f"[SAVED] {CLASS_OUT}")

    # 8. Self-test inference on 10 known brands
    print(f"\n{'='*60}")
    print(f"  SELF-TEST: 10 Inference Samples (model.eval)")
    print(f"{'='*60}")
    model.eval()

    test_samples = [
        "Napa","Azipen","Omeprazol","Amoxil","Ciprocin",
        "Clavam","Neoceptin","Diclofen","Cefim","Kenacort"
    ]
    correct_self = 0
    for brand in test_samples:
        arr    = make_image(brand, augment=False)
        tensor = torch.from_numpy(arr.transpose(2,0,1)).unsqueeze(0).to(dev)
        with torch.no_grad():
            logits = model(tensor)
            probs  = torch.softmax(logits, 1)[0]
            top3   = torch.topk(probs, 3)

        pred_brand   = IDX2CLS[top3.indices[0].item()]
        pred_conf    = top3.values[0].item() * 100
        pred_generic = MEDICINE_DB.get(pred_brand, "Unknown")
        ok = "[PASS]" if pred_brand == brand else "[FAIL]"
        if pred_brand == brand:
            correct_self += 1
        print(f"  {ok} '{brand:<12}' -> '{pred_brand:<12}' ({pred_conf:5.1f}%)  [{pred_generic}]")

    print(f"\n  Self-Test Score: {correct_self}/{len(test_samples)} "
          f"({correct_self/len(test_samples)*100:.0f}%)")
    print(f"\n[COMPLETE] Training done in {(time.time()-t0)/60:.1f} min")
    print(f"[RESULT]   Test Acc={test_acc*100:.2f}%  Val Acc={best_vacc*100:.2f}%  "
          f"Top5={top5_acc*100:.2f}%  MacroF1={mf1*100:.2f}%")

    return test_acc, best_vacc, mf1


if __name__ == "__main__":
    main()
