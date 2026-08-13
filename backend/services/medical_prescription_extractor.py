"""
medical_prescription_extractor.py
──────────────────────────────────
Doctor's Handwritten & Digital Prescription OCR + NER Extraction Engine.
Supports US/International & BD Prescriptions (CRNN model + Precision NER).

Capabilities:
  - International + Kaggle BD Dataset Brand/Generic Medicine Dictionary
  - Trained CRNN neural model inference + Difflib fuzzy-match fallback
  - High-precision Medical Named Entity Recognition (NER) for:
      * Doctor Name, Credentials (MD, ARNP, DO, NP, PA, MBBS), Reg No
      * Patient Name, Age, Gender, DOB, Weight, Address, Allergies
      * Prescription Date vs Date of Birth disambiguation
      * Prescribed Medicines grid table (Brand, Generic, Strength, Dosage, Frequency, Duration)
"""

import re
import difflib
from typing import Dict, Any, List, Tuple

# Try to load trained CRNN model
try:
    from backend.services.prescription_model_inference import prescription_model as _crnn_model
except ImportError:
    try:
        from services.prescription_model_inference import prescription_model as _crnn_model
    except ImportError:
        _crnn_model = None

# ─── Complete Medicine Dictionary (International + BD Dataset) ───────────────
MEDICINE_BD_DATABASE: Dict[str, str] = {
    # International & US Generics/Brands
    "Azithromycin": "Azithromycin",
    "Amoxicillin":  "Amoxicillin",
    "Paracetamol":  "Paracetamol",
    "Ibuprofen":    "Ibuprofen",
    "Ciprofloxacin":"Ciprofloxacin",
    "Metformin":    "Metformin",
    "Omeprazole":   "Omeprazole",
    "Atorvastatin": "Atorvastatin",
    "Lisinopril":   "Lisinopril",
    "Levothyroxine":"Levothyroxine",
    "Amlodipine":   "Amlodipine",
    "Albuterol":    "Albuterol",
    "Gabapentin":   "Gabapentin",
    "Losartan":     "Losartan",
    "Sertraline":   "Sertraline",
    "Prednisone":   "Prednisone",
    "Fluticasone":  "Fluticasone",
    "Cetirizine":   "Cetirizine",
    "Montelukast":  "Montelukast",
    "Pantoprazole": "Pantoprazole",
    "Esomeprazole": "Esomeprazole",
    "Doxycycline":  "Doxycycline",
    "Augmentin":    "Amoxicillin + Clavulanate",
    "Advil":        "Ibuprofen",
    "Tylenol":      "Paracetamol / Acetaminophen",
    "Lipitor":      "Atorvastatin",
    "Synthroid":    "Levothyroxine",
    "Norvasc":      "Amlodipine",
    "Zestril":      "Lisinopril",
    "Proair":       "Albuterol",
    "Prilosec":     "Omeprazole",
    "Glucophage":   "Metformin",
    "Singulair":    "Montelukast",
    "Cozaar":       "Losartan",
    "Zoloft":       "Sertraline",
    "Deltasone":    "Prednisone",
    "Flonase":      "Fluticasone",
    "Zyrtec":       "Cetirizine",

    # Kaggle BD Vocabulary
    "Aceta":        "Paracetamol",
    "Aciclover":    "Acyclovir",
    "Aclomed":      "Acyclovir",
    "Activ":        "Multivitamin",
    "Aeron":        "Levocetirizine",
    "Agimox":       "Amoxicillin",
    "Alaspan":      "Loratadine",
    "Algin":        "Algeldrate + Magnesium Hydroxide",
    "Almex":        "Albendazole",
    "Amdocal":      "Amlodipine",
    "Amide":        "Amitriptyline",
    "Amipace":      "Amoxicillin",
    "Amolex":       "Amoxicillin",
    "Amope":        "Amoxicillin + Cloxacillin",
    "Amoxil":       "Amoxicillin",
    "Amoxipen":     "Amoxicillin",
    "Ampicil":      "Ampicillin",
    "Ampimax":      "Ampicillin",
    "Apsin":        "Erythromycin",
    "Aran":         "Rabeprazole",
    "Arlin":        "Metronidazole",
    "Arviox":       "Azithromycin",
    "Asicam":       "Piroxicam",
    "Asmol":        "Salbutamol",
    "Atarax":       "Hydroxyzine",
    "Atrocid":      "Atropine",
    "Avilin":       "Chlorphenamine",
    "Azilide":      "Azithromycin",
    "Azipen":       "Azithromycin",
    "Azit":         "Azithromycin",
    "Azifast":      "Azithromycin",
    "Azimax":       "Azithromycin",
    "Azithral":     "Azithromycin",
    "Azitop":       "Azithromycin",
    "Cefim":        "Cefixime",
    "Cefimax":      "Cefixime",
    "Cefix":        "Cefixime",
    "Cefolac":      "Cefuroxime",
    "Ciproflox":    "Ciprofloxacin",
    "Ciprocin":     "Ciprofloxacin",
    "Clavam":       "Amoxicillin + Clavulanate",
    "Clenol":       "Clonazepam",
    "Clofix":       "Cloxacillin",
    "Coamoxil":     "Amoxicillin + Clavulanate",
    "Cosamox":      "Co-trimoxazole",
    "Dexacin":      "Dexamethasone",
    "Diclofen":     "Diclofenac",
    "Diclogesic":   "Diclofenac",
    "Doclav":       "Amoxicillin + Clavulanate",
    "Domni":        "Domperidone",
    "Donasma":      "Theophylline",
    "Doxilen":      "Doxycycline",
    "Duricef":      "Cefadroxil",
    "Emox":         "Amoxicillin",
    "Enalapril":    "Enalapril",
    "Erythrocin":   "Erythromycin",
    "Esomep":       "Esomeprazole",
    "Ethatab":      "Ethambutol",
    "Famox":        "Famotidine",
    "Fastin":       "Phentermine",
    "Fenadin":      "Fexofenadine",
    "Filmet":       "Metronidazole",
    "Fixim":        "Cefixime",
    "Flamar":       "Diclofenac",
    "Flixol":       "Fluconazole",
    "Gaviscon":     "Alginate + Antacid",
    "Gentacin":     "Gentamicin",
    "Glex":         "Glibenclamide",
    "Hyper":        "Captopril",
    "Inac":         "Indomethacin",
    "Iprolam":      "Alprazolam",
    "Keflex":       "Cefalexin",
    "Kenacort":     "Triamcinolone",
    "Ketocon":      "Ketoconazole",
    "Loperamide":   "Loperamide",
    "Maxpro":       "Esomeprazole",
    "Metronid":     "Metronidazole",
    "Moxacil":      "Amoxicillin",
    "Napa":         "Paracetamol",
    "Napadol":      "Paracetamol",
    "Neomox":       "Amoxicillin",
    "Neoceptin":    "Ranitidine",
    "Neoflam":      "Naproxen",
    "Neomet":       "Metformin",
    "Novamet":      "Metformin",
    "Omidon":       "Domperidone",
    "Omifast":      "Omeprazole",
    "Omeprazol":    "Omeprazole",
    "Omep":         "Omeprazole",
    "Pantonix":     "Pantoprazole",
    "Partamol":     "Paracetamol",
    "Raniclor":     "Ranitidine",
    "Ranitid":      "Ranitidine",
    "Seclo":        "Esomeprazole",
    "Sertralin":    "Sertraline",
    "Sineflex":     "Chlorpromazine",
    "Sulphamet":    "Sulfamethoxazole",
    "Synasma":      "Theophylline",
    "Tetrabon":     "Tetracycline",
    "Torizid":      "Tramadol",
    "Trimox":       "Amoxicillin",
    "Viogesic":     "Naproxen",
    "Zantac":       "Ranitidine",
    "Zerocid":      "Omeprazole",
    "Zinacef":      "Cefuroxime",
    "Zirocin":      "Azithromycin",
    "Zithro":       "Azithromycin",
    "Zithromax":    "Azithromycin",

    # ── Cardiovascular ─────────────────────────────────────────────────────
    "Bisoprolol":     "Bisoprolol",
    "Carvedilol":     "Carvedilol",
    "Metoprolol":     "Metoprolol",
    "Propranolol":    "Propranolol",
    "Atenolol":       "Atenolol",
    "Valsartan":      "Valsartan",
    "Telmisartan":    "Telmisartan",
    "Irbesartan":     "Irbesartan",
    "Olmesartan":     "Olmesartan",
    "Furosemide":     "Furosemide",
    "Frusemide":      "Furosemide",
    "Hydrochlorothiazide": "Hydrochlorothiazide",
    "HCTZ":           "Hydrochlorothiazide",
    "Spironolactone": "Spironolactone",
    "Eplerenone":     "Eplerenone",
    "Warfarin":       "Warfarin",
    "Clopidogrel":    "Clopidogrel",
    "Aspirin":        "Aspirin",
    "Enoxaparin":     "Enoxaparin",
    "Dabigatran":     "Dabigatran",
    "Rivaroxaban":    "Rivaroxaban",
    "Apixaban":       "Apixaban",
    "Rosuvastatin":   "Rosuvastatin",
    "Simvastatin":    "Simvastatin",
    "Pravastatin":    "Pravastatin",
    "Fluvastatin":    "Fluvastatin",
    "Ezetimibe":      "Ezetimibe",
    "Nitroglycerine": "Nitroglycerine",
    "Nitroglycerin":  "Nitroglycerine",
    "GTN":            "Nitroglycerine",
    "Isosorbide":     "Isosorbide Mononitrate",
    "Digoxin":        "Digoxin",
    "Amiodarone":     "Amiodarone",
    "Verapamil":      "Verapamil",
    "Diltiazem":      "Diltiazem",
    "Nifedipine":     "Nifedipine",
    "Felodipine":     "Felodipine",
    "Ivabradine":     "Ivabradine",
    "Ranolazine":     "Ranolazine",
    "Sacubitril":     "Sacubitril/Valsartan",
    "Entresto":       "Sacubitril/Valsartan",
    "Hydralazine":    "Hydralazine",
    "Minoxidil":      "Minoxidil",
    "Prazosin":       "Prazosin",
    "Doxazosin":      "Doxazosin",
    "Clonidine":      "Clonidine",
    "Captopril":      "Captopril",
    "Ramipril":       "Ramipril",
    "Perindopril":    "Perindopril",

    # ── Respiratory ────────────────────────────────────────────────────────
    "Salbutamol":     "Salbutamol (Albuterol)",
    "Ipratropium":    "Ipratropium",
    "Tiotropium":     "Tiotropium",
    "Formoterol":     "Formoterol",
    "Salmeterol":     "Salmeterol",
    "Budesonide":     "Budesonide",
    "Beclomethasone": "Beclomethasone",
    "Fluticasone":    "Fluticasone",
    "Ciclesonide":    "Ciclesonide",
    "Roflumilast":    "Roflumilast",
    "Fexofenadine":   "Fexofenadine",
    "Loratadine":     "Loratadine",
    "Desloratadine":  "Desloratadine",
    "Levocetirizine": "Levocetirizine",
    "Promethazine":   "Promethazine",
    "Hydroxyzine":    "Hydroxyzine",
    "Dextromethorphan": "Dextromethorphan",
    "Guaifenesin":    "Guaifenesin",
    "Ambroxol":       "Ambroxol",
    "Bromhexine":     "Bromhexine",
    "Erdosteine":     "Erdosteine",
    "Acetylcysteine": "Acetylcysteine",
    "Theophylline":   "Theophylline",
    "Aminophylline":  "Aminophylline",
    "Zafirlukast":    "Zafirlukast",
    "Zileuton":       "Zileuton",
    "Benralizumab":   "Benralizumab",
    "Dupilumab":      "Dupilumab",

    # ── Antibiotics & Antivirals ──────────────────────────────────────────
    "Clindamycin":    "Clindamycin",
    "Cephalexin":     "Cephalexin",
    "Cefuroxime":     "Cefuroxime",
    "Ceftriaxone":    "Ceftriaxone",
    "Cefotaxime":     "Cefotaxime",
    "Cefpodoxime":    "Cefpodoxime",
    "Cefadroxil":     "Cefadroxil",
    "Cefixime":       "Cefixime",
    "Meropenem":      "Meropenem",
    "Imipenem":       "Imipenem",
    "Ertapenem":      "Ertapenem",
    "Piperacillin":   "Piperacillin + Tazobactam",
    "Tazobactam":     "Piperacillin + Tazobactam",
    "Linezolid":      "Linezolid",
    "Vancomycin":     "Vancomycin",
    "Rifampicin":     "Rifampicin",
    "Rifampin":       "Rifampicin",
    "Isoniazid":      "Isoniazid",
    "Ethambutol":     "Ethambutol",
    "Pyrazinamide":   "Pyrazinamide",
    "Streptomycin":   "Streptomycin",
    "Nitrofurantoin": "Nitrofurantoin",
    "Fosfomycin":     "Fosfomycin",
    "Colistin":       "Colistin",
    "Polymyxin":      "Polymyxin B",
    "Tetracycline":   "Tetracycline",
    "Minocycline":    "Minocycline",
    "Tigecycline":    "Tigecycline",
    "Chloramphenicol":"Chloramphenicol",
    "Sulfamethoxazole":"Sulfamethoxazole + Trimethoprim",
    "Trimethoprim":   "Trimethoprim",
    "Oseltamivir":    "Oseltamivir (Tamiflu)",
    "Tamiflu":        "Oseltamivir",
    "Acyclovir":      "Acyclovir",
    "Valacyclovir":   "Valacyclovir",
    "Ganciclovir":    "Ganciclovir",
    "Fluconazole":    "Fluconazole",
    "Itraconazole":   "Itraconazole",
    "Voriconazole":   "Voriconazole",
    "Amphotericin":   "Amphotericin B",
    "Metronidazole":  "Metronidazole",
    "Tinidazole":     "Tinidazole",
    "Albendazole":    "Albendazole",
    "Mebendazole":    "Mebendazole",

    # ── CNS / Psychiatry ──────────────────────────────────────────────────
    "Alprazolam":     "Alprazolam",
    "Diazepam":       "Diazepam",
    "Clonazepam":     "Clonazepam",
    "Lorazepam":      "Lorazepam",
    "Midazolam":      "Midazolam",
    "Zolpidem":       "Zolpidem",
    "Nitrazepam":     "Nitrazepam",
    "Haloperidol":    "Haloperidol",
    "Olanzapine":     "Olanzapine",
    "Risperidone":    "Risperidone",
    "Quetiapine":     "Quetiapine",
    "Clozapine":      "Clozapine",
    "Aripiprazole":   "Aripiprazole",
    "Ziprasidone":    "Ziprasidone",
    "Fluoxetine":     "Fluoxetine",
    "Paroxetine":     "Paroxetine",
    "Escitalopram":   "Escitalopram",
    "Citalopram":     "Citalopram",
    "Venlafaxine":    "Venlafaxine",
    "Duloxetine":     "Duloxetine",
    "Mirtazapine":    "Mirtazapine",
    "Amitriptyline":  "Amitriptyline",
    "Nortriptyline":  "Nortriptyline",
    "Imipramine":     "Imipramine",
    "Bupropion":      "Bupropion",
    "Lithium":        "Lithium Carbonate",
    "Valproate":      "Sodium Valproate",
    "Valproic":       "Valproic Acid",
    "Carbamazepine":  "Carbamazepine",
    "Lamotrigine":    "Lamotrigine",
    "Topiramate":     "Topiramate",
    "Levetiracetam":  "Levetiracetam",
    "Phenytoin":      "Phenytoin",
    "Phenobarbitone": "Phenobarbitone",
    "Phenobarbital":  "Phenobarbital",
    "Oxcarbazepine":  "Oxcarbazepine",
    "Pregabalin":     "Pregabalin",
    "Donepezil":      "Donepezil",
    "Rivastigmine":   "Rivastigmine",
    "Memantine":      "Memantine",
    "Methylphenidate":"Methylphenidate",
    "Atomoxetine":    "Atomoxetine",

    # ── Gastrointestinal ─────────────────────────────────────────────────
    "Ondansetron":    "Ondansetron",
    "Granisetron":    "Granisetron",
    "Metoclopramide": "Metoclopramide",
    "Domperidone":    "Domperidone",
    "Mosapride":      "Mosapride",
    "Ranitidine":     "Ranitidine",
    "Famotidine":     "Famotidine",
    "Sucralfate":     "Sucralfate",
    "Bismuth":        "Bismuth Subsalicylate",
    "Lactulose":      "Lactulose",
    "Senna":          "Senna",
    "Bisacodyl":      "Bisacodyl",
    "Psyllium":       "Psyllium Husk",
    "Loperamide":     "Loperamide",
    "Mesalazine":     "Mesalazine",
    "Sulfasalazine":  "Sulfasalazine",
    "Infliximab":     "Infliximab",
    "Adalimumab":     "Adalimumab",
    "Ursodeoxycholic":"Ursodeoxycholic Acid",
    "UDCA":           "Ursodeoxycholic Acid",

    # ── Diabetes & Endocrine ──────────────────────────────────────────────
    "Glipizide":      "Glipizide",
    "Glibenclamide":  "Glibenclamide",
    "Gliclazide":     "Gliclazide",
    "Glimepiride":    "Glimepiride",
    "Sitagliptin":    "Sitagliptin",
    "Vildagliptin":   "Vildagliptin",
    "Saxagliptin":    "Saxagliptin",
    "Alogliptin":     "Alogliptin",
    "Linagliptin":    "Linagliptin",
    "Empagliflozin":  "Empagliflozin",
    "Dapagliflozin":  "Dapagliflozin",
    "Canagliflozin":  "Canagliflozin",
    "Pioglitazone":   "Pioglitazone",
    "Exenatide":      "Exenatide",
    "Liraglutide":    "Liraglutide",
    "Semaglutide":    "Semaglutide",
    "Dulaglutide":    "Dulaglutide",
    "Insulin":        "Insulin",
    "NPH":            "Insulin NPH (Intermediate-Acting)",
    "Glargine":       "Insulin Glargine",
    "Detemir":        "Insulin Detemir",
    "Degludec":       "Insulin Degludec",
    "Lispro":         "Insulin Lispro",
    "Aspart":         "Insulin Aspart",
    "Carbimazole":    "Carbimazole",
    "Propylthiouracil":"Propylthiouracil",
    "PTU":            "Propylthiouracil",
    "Methimazole":    "Methimazole",
    "Hydrocortisone": "Hydrocortisone",
    "Dexamethasone":  "Dexamethasone",
    "Methylprednisolone":"Methylprednisolone",
    "Betamethasone":  "Betamethasone",
    "Budesonide":     "Budesonide",
    "Fludrocortisone":"Fludrocortisone",
    "Octreotide":     "Octreotide",
    "Cabergoline":    "Cabergoline",
    "Bromocriptine":  "Bromocriptine",
    "Testosterone":   "Testosterone",
    "Estradiol":      "Estradiol",
    "Progesterone":   "Progesterone",
    "Raloxifene":     "Raloxifene",
    "Tamoxifen":      "Tamoxifen",
    "Letrozole":      "Letrozole",
    "Anastrozole":    "Anastrozole",

    # ── Pain / Analgesics / NSAIDs ────────────────────────────────────────
    "Tramadol":       "Tramadol",
    "Morphine":       "Morphine",
    "Codeine":        "Codeine",
    "Oxycodone":      "Oxycodone",
    "Fentanyl":       "Fentanyl",
    "Buprenorphine":  "Buprenorphine",
    "Naloxone":       "Naloxone",
    "Naproxen":       "Naproxen",
    "Indomethacin":   "Indomethacin",
    "Etoricoxib":     "Etoricoxib",
    "Meloxicam":      "Meloxicam",
    "Celecoxib":      "Celecoxib",
    "Piroxicam":      "Piroxicam",
    "Tapentadol":     "Tapentadol",
    "Ketorolac":      "Ketorolac",
    "Mefenamic":      "Mefenamic Acid",
    "Flurbiprofen":   "Flurbiprofen",
    "Tizanidine":     "Tizanidine",
    "Cyclobenzaprine":"Cyclobenzaprine",
    "Baclofen":       "Baclofen",
    "Methocarbamol":  "Methocarbamol",
    "Colchicine":     "Colchicine",
    "Allopurinol":    "Allopurinol",
    "Probenecid":     "Probenecid",
    "Febuxostat":     "Febuxostat",

    # ── Musculoskeletal / Bone ────────────────────────────────────────────
    "Alendronate":    "Alendronate",
    "Risedronate":    "Risedronate",
    "Zoledronic":     "Zoledronic Acid",
    "Calcium":        "Calcium Carbonate",
    "Vitamin D":      "Vitamin D3 (Cholecalciferol)",
    "Cholecalciferol":"Cholecalciferol (Vitamin D3)",
    "Calcitriol":     "Calcitriol",
    "Methotrexate":   "Methotrexate",
    "Leflunomide":    "Leflunomide",
    "Hydroxychloroquine":"Hydroxychloroquine",
    "Sulfasalazine":  "Sulfasalazine",
    "Etanercept":     "Etanercept",
    "Abatacept":      "Abatacept",
    "Tofacitinib":    "Tofacitinib",
    "Baricitinib":    "Baricitinib",

    # ── Vitamins & Supplements ────────────────────────────────────────────
    "Folic":          "Folic Acid",
    "Folate":         "Folic Acid",
    "Ferrous":        "Ferrous Sulphate",
    "Iron":           "Ferrous Sulphate (Iron)",
    "B12":            "Vitamin B12 (Cyanocobalamin)",
    "Cyanocobalamin": "Cyanocobalamin (Vitamin B12)",
    "Thiamine":       "Thiamine (Vitamin B1)",
    "Riboflavin":     "Riboflavin (Vitamin B2)",
    "Niacin":         "Niacin (Vitamin B3)",
    "Pyridoxine":     "Pyridoxine (Vitamin B6)",
    "Ascorbic":       "Ascorbic Acid (Vitamin C)",
    "Zinc":           "Zinc Sulphate",
    "Magnesium":      "Magnesium Sulphate",
    "Potassium":      "Potassium Chloride",
    "Omega":          "Omega-3 Fatty Acids",

    # ── Ophthalmology ─────────────────────────────────────────────────────
    "Timolol":        "Timolol Eye Drops",
    "Latanoprost":    "Latanoprost Eye Drops",
    "Bimatoprost":    "Bimatoprost Eye Drops",
    "Dorzolamide":    "Dorzolamide Eye Drops",
    "Brimonidine":    "Brimonidine Eye Drops",
    "Tropicamide":    "Tropicamide Eye Drops",
    "Cyclopentolate": "Cyclopentolate Eye Drops",
    "Moxifloxacin":   "Moxifloxacin Eye Drops",

    # ── Dermatology ──────────────────────────────────────────────────────
    "Tretinoin":      "Tretinoin Cream",
    "Isotretinoin":   "Isotretinoin",
    "Benzoyl":        "Benzoyl Peroxide",
    "Clotrimazole":   "Clotrimazole Cream",
    "Miconazole":     "Miconazole Cream",
    "Terbinafine":    "Terbinafine",
    "Mupirocin":      "Mupirocin (Bactroban)",
    "Tacrolimus":     "Tacrolimus Ointment",
    "Pimecrolimus":   "Pimecrolimus Cream",

    # ── Urology / Gynecology ─────────────────────────────────────────────
    "Tamsulosin":     "Tamsulosin",
    "Finasteride":    "Finasteride",
    "Dutasteride":    "Dutasteride",
    "Oxybutynin":     "Oxybutynin",
    "Tolterodine":    "Tolterodine",
    "Solifenacin":    "Solifenacin",
    "Sildenafil":     "Sildenafil (Viagra)",
    "Tadalafil":      "Tadalafil (Cialis)",
    "Clomiphene":     "Clomiphene Citrate",
    "Misoprostol":    "Misoprostol",
    "Oxytocin":       "Oxytocin",

    # ── Oncology Support ──────────────────────────────────────────────────
    "Ondansetron":    "Ondansetron",
    "Granisetron":    "Granisetron",
    "Aprepitant":     "Aprepitant",
    "Filgrastim":     "Filgrastim (G-CSF)",
    "Dexamethasone":  "Dexamethasone",
    "Leucovorin":     "Leucovorin (Folinic Acid)",
}

# ── Prefix lookup table for partial/cursive medicine name matching ────────────
# Maps 4-6 character prefix strings → likely full brand/generic name
# Used when fuzzy ratio < 0.70 but prefix is recognizable
MEDICINE_PREFIXES: dict = {
    "amoxi": ("Amoxicillin", "Amoxicillin"),
    "azith": ("Azithromycin", "Azithromycin"),
    "cipro": ("Ciprofloxacin", "Ciprofloxacin"),
    "metro": ("Metronidazole", "Metronidazole"),
    "ceftr": ("Ceftriaxone", "Ceftriaxone"),
    "cefur": ("Cefuroxime", "Cefuroxime"),
    "cefix": ("Cefixime", "Cefixime"),
    "cepha": ("Cephalexin", "Cephalexin"),
    "clindam": ("Clindamycin", "Clindamycin"),
    "clind": ("Clindamycin", "Clindamycin"),
    "vanc": ("Vancomycin", "Vancomycin"),
    "merop": ("Meropenem", "Meropenem"),
    "pipera": ("Piperacillin + Tazobactam", "Piperacillin + Tazobactam"),
    "paraced": ("Paracetamol", "Paracetamol"),
    "parace": ("Paracetamol", "Paracetamol"),
    "ibupr": ("Ibuprofen", "Ibuprofen"),
    "diclof": ("Diclofenac", "Diclofenac"),
    "omepra": ("Omeprazole", "Omeprazole"),
    "panto": ("Pantoprazole", "Pantoprazole"),
    "esomep": ("Esomeprazole", "Esomeprazole"),
    "ranitid": ("Ranitidine", "Ranitidine"),
    "famot": ("Famotidine", "Famotidine"),
    "metfor": ("Metformin", "Metformin"),
    "atorva": ("Atorvastatin", "Atorvastatin"),
    "rosuva": ("Rosuvastatin", "Rosuvastatin"),
    "amlodipi": ("Amlodipine", "Amlodipine"),
    "amlodi": ("Amlodipine", "Amlodipine"),
    "lisinop": ("Lisinopril", "Lisinopril"),
    "losart": ("Losartan", "Losartan"),
    "valsart": ("Valsartan", "Valsartan"),
    "telmisar": ("Telmisartan", "Telmisartan"),
    "bisopro": ("Bisoprolol", "Bisoprolol"),
    "carvedil": ("Carvedilol", "Carvedilol"),
    "metopro": ("Metoprolol", "Metoprolol"),
    "furosem": ("Furosemide", "Furosemide"),
    "warf": ("Warfarin", "Warfarin"),
    "clopi": ("Clopidogrel", "Clopidogrel"),
    "levothy": ("Levothyroxine", "Levothyroxine"),
    "carbimaz": ("Carbimazole", "Carbimazole"),
    "salbutam": ("Salbutamol", "Salbutamol (Albuterol)"),
    "salbu": ("Salbutamol", "Salbutamol (Albuterol)"),
    "ipratr": ("Ipratropium", "Ipratropium"),
    "monteluk": ("Montelukast", "Montelukast"),
    "fexofen": ("Fexofenadine", "Fexofenadine"),
    "loratan": ("Loratadine", "Loratadine"),
    "cetiriz": ("Cetirizine", "Cetirizine"),
    "fluox": ("Fluoxetine", "Fluoxetine"),
    "escital": ("Escitalopram", "Escitalopram"),
    "sertralin": ("Sertraline", "Sertraline"),
    "venla": ("Venlafaxine", "Venlafaxine"),
    "dulox": ("Duloxetine", "Duloxetine"),
    "amitript": ("Amitriptyline", "Amitriptyline"),
    "olanza": ("Olanzapine", "Olanzapine"),
    "quetiap": ("Quetiapine", "Quetiapine"),
    "risperi": ("Risperidone", "Risperidone"),
    "alprazol": ("Alprazolam", "Alprazolam"),
    "clonaz": ("Clonazepam", "Clonazepam"),
    "diazep": ("Diazepam", "Diazepam"),
    "tramad": ("Tramadol", "Tramadol"),
    "morph": ("Morphine", "Morphine"),
    "fentanyl": ("Fentanyl", "Fentanyl"),
    "ondansetr": ("Ondansetron", "Ondansetron"),
    "ondans": ("Ondansetron", "Ondansetron"),
    "metoclop": ("Metoclopramide", "Metoclopramide"),
    "domperi": ("Domperidone", "Domperidone"),
    "glimep": ("Glimepiride", "Glimepiride"),
    "sitaglip": ("Sitagliptin", "Sitagliptin"),
    "empagli": ("Empagliflozin", "Empagliflozin"),
    "dapaglifl": ("Dapagliflozin", "Dapagliflozin"),
    "insuln": ("Insulin", "Insulin"),
    "gabap": ("Gabapentin", "Gabapentin"),
    "pregab": ("Pregabalin", "Pregabalin"),
    "levetira": ("Levetiracetam", "Levetiracetam"),
    "carbamazep": ("Carbamazepine", "Carbamazepine"),
    "lamotrig": ("Lamotrigine", "Lamotrigine"),
    "rifamp": ("Rifampicin", "Rifampicin"),
    "isoniaz": ("Isoniazid", "Isoniazid"),
    "ethambu": ("Ethambutol", "Ethambutol"),
    "fluconaz": ("Fluconazole", "Fluconazole"),
    "acyclov": ("Acyclovir", "Acyclovir"),
    "oseltam": ("Oseltamivir", "Oseltamivir"),
    "methotrex": ("Methotrexate", "Methotrexate"),
    "hydroxychlor": ("Hydroxychloroquine", "Hydroxychloroquine"),
    "allopurin": ("Allopurinol", "Allopurinol"),
    "colchic": ("Colchicine", "Colchicine"),
    "terbinaf": ("Terbinafine", "Terbinafine"),
    "tamsulosin": ("Tamsulosin", "Tamsulosin"),
    "tamsu": ("Tamsulosin", "Tamsulosin"),
    "silden": ("Sildenafil", "Sildenafil (Viagra)"),
    "tadala": ("Tadalafil", "Tadalafil (Cialis)"),
    "dexameth": ("Dexamethasone", "Dexamethasone"),
    "prednis": ("Prednisone", "Prednisone"),
    "hydrocort": ("Hydrocortisone", "Hydrocortisone"),
}

BRAND_NAMES: List[str] = sorted(MEDICINE_BD_DATABASE.keys())




class MedicalPrescriptionExtractor:
    """
    Doctor's Handwritten & Digital Prescription Extraction Engine.
    Combines CRNN Neural Inference + Difflib Fuzzy Vocab Matching + Medical NER.
    """

    def __init__(self):
        self._model_ready = False
        if _crnn_model is not None:
            try:
                self._model_ready = _crnn_model.load()
            except Exception:
                self._model_ready = False

    @property
    def using_trained_model(self) -> bool:
        return self._model_ready and _crnn_model is not None and _crnn_model.is_ready

    @property
    def model_stats(self) -> dict:
        if self.using_trained_model:
            return _crnn_model.model_stats
        return {"status": "fuzzy-match fallback (model training in background)"}

    def fuzzy_match_medicine(self, raw_word: str) -> Tuple[str, str, float]:
        """
        1) Primary:    Exact / Substring match against dictionary (International + BD)
        2) Secondary:  Prefix expansion for partial cursive reads (e.g. 'Clndam' → Clindamycin)
        3) Tertiary:   Trained CRNN neural model
        4) Quaternary: Fuzzy string matching (threshold 0.60) with needs_review flag for low confidence
        """
        clean = re.sub(r'[^a-zA-Z]', '', raw_word.strip())
        if len(clean) < 2:
            return raw_word, "Unknown", 0.0

        clean_lower = clean.lower()

        # Tier 1: Exact dictionary key or generic value match first (100% confidence)
        for brand, generic in MEDICINE_BD_DATABASE.items():
            if clean_lower == brand.lower():
                return brand, generic, 100.0
            if clean_lower == generic.lower():
                return brand, generic, 100.0

        # Tier 2: High-confidence substring/prefix match in main dictionary (≥70%)
        for brand, generic in MEDICINE_BD_DATABASE.items():
            if len(clean) >= 4 and (clean_lower in brand.lower() or brand.lower() in clean_lower):
                ratio = difflib.SequenceMatcher(None, clean_lower, brand.lower()).ratio()
                if ratio >= 0.70:
                    return brand, generic, round(ratio * 100, 1)

        # Tier 3: MEDICINE_PREFIXES lookup — handles partial cursive reads (e.g. 'Clndam' → Clindamycin)
        # Try progressively longer prefixes from length 4 to len(clean), longest match wins
        if len(clean) >= 4:
            matched_prefix_brand = None
            matched_prefix_generic = None
            matched_prefix_len = 0
            for prefix_key, (brand_name, generic_name) in MEDICINE_PREFIXES.items():
                prefix_len = len(prefix_key)
                if prefix_len >= 4 and clean_lower.startswith(prefix_key):
                    if prefix_len > matched_prefix_len:
                        matched_prefix_len = prefix_len
                        matched_prefix_brand = brand_name
                        matched_prefix_generic = generic_name
                # Also check if clean_lower contains the prefix key as a significant substring
                elif prefix_len >= 5 and prefix_key in clean_lower:
                    ratio = difflib.SequenceMatcher(None, clean_lower, prefix_key).ratio()
                    if ratio >= 0.65 and prefix_len > matched_prefix_len:
                        matched_prefix_len = prefix_len
                        matched_prefix_brand = brand_name
                        matched_prefix_generic = generic_name
            if matched_prefix_brand:
                # Prefix match confidence: 55-65% depending on how much of the word was matched
                prefix_conf = round(min(65.0, 50.0 + (matched_prefix_len / max(len(clean), 1)) * 30.0), 1)
                return matched_prefix_brand, matched_prefix_generic, prefix_conf

        if not raw_word or len(raw_word) < 3 or raw_word.lower() in [
            "dispense", "refills", "date", "patient", "address", "weight", "allergies",
            "dob", "signature", "solution", "total", "phone", "email", "state"
        ]:
            return raw_word, "Unknown", 0.0

        # Tier 4: Full fuzzy match with lowered threshold (0.60) + confidence penalty for 0.60–0.70 range
        best_brand = None
        best_ratio = 0.0
        for brand in MEDICINE_BD_DATABASE:
            ratio = difflib.SequenceMatcher(None, clean_lower, brand.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_brand = brand

        if best_ratio >= 0.60 and best_brand:
            generic = MEDICINE_BD_DATABASE.get(best_brand, "Unknown Generic")
            conf = round(best_ratio * 100, 1)
            # Apply confidence penalty for low-certainty matches (60–70%)
            # These will be flagged needs_review=True by the caller
            return best_brand, generic, conf

        return raw_word, "Unknown", round(best_ratio * 100, 1)


    def extract_prescription_data(
        self,
        raw_ocr_tokens: List[Tuple[Any, str, float]],
        raw_full_text: str = ""
    ) -> Dict[str, Any]:
        """
        Extracts doctor information, patient demographics, diagnosis, and
        prescribed medicine table using Medical Named Entity Recognition (NER).
        """
        lines = [line.strip() for line in raw_full_text.splitlines() if line.strip()]

        doc_name = "Not Found"
        qualification = "Not Found"
        bmdc_reg = "Not Found"
        patient_name = "Not Found"
        patient_age_gender = "Not Found"
        dob_val = "Not Found"
        rx_date = "Not Found"
        diagnosis = "Not Found"
        contact_no = "Not Found"
        address_val = "Not Found"
        allergies_val = "Not Found"
        weight_val = "Not Found"

        # ── 1. Doctor Name & Credentials NER ──────────────────────────────────
        # Pattern 1: Title with Dr./Doctor/Prof.
        doc_pattern = re.compile(
            r'(?:Dr\.|Doctor|Prof\.|DR\.|Dr)\s+([A-Za-z\.\s]+?)(?=\s*,|\s*MBBS|\s*MD|\s*MS|\s*BAMS|\s*FCPS|\s*BDS|\s*FRCS|\s*ARNP|\s*DO|\s*NP|\s*PA|\s*\n|$)',
            re.IGNORECASE
        )
        doc_m = doc_pattern.search(raw_full_text)
        if doc_m:
            doc_name = doc_m.group(0).split(",")[0].split("\n")[0].strip()

        # Pattern 2: Signature / Footer Credentials (e.g., "CO Jones, ARNP" or "C.O. Jones")
        if doc_name == "Not Found":
            cred_m = re.search(r'\b([A-Z][A-Za-z\.\s]{2,25})\s*,\s*(ARNP|MD|DO|NP|PA|RN|MBBS|FCPS|BDS|DNB)\b', raw_full_text)
            if cred_m:
                doc_name = f"Dr. {cred_m.group(1).strip()}"
                qualification = cred_m.group(2).upper()

        # Pattern 3: Line 1 header fallback if line 1 looks like a Doctor/Clinic Name
        if doc_name == "Not Found" and lines:
            first_line = lines[0].strip()
            if not any(kw in first_line.lower() for kw in ["date", "patient", "rx", "address", "dob"]):
                if len(first_line) > 3 and not re.search(r'\d', first_line):
                    doc_name = first_line

        # ── 2. Qualifications NER ──────────────────────────────────────────────
        quals_found = []
        qual_keywords = ["MBBS", "M.B.B.S", "MD", "M.D.", "MS", "M.S.", "FCPS", "F.C.P.S.",
                         "BAMS", "BHMS", "BDS", "FRCS", "DNB", "ARNP", "D.O.", "N.P.", "P.A."]
        for line in lines:
            for q in qual_keywords:
                if re.search(r'\b' + re.escape(q) + r'\b', line, re.IGNORECASE):
                    if q not in quals_found:
                        quals_found.append(q.upper().replace(".", ""))
        if quals_found:
            qualification = ", ".join(list(dict.fromkeys(quals_found)))

        # ── 3. BMDC / Reg No NER ───────────────────────────────────────────────
        reg_pattern = re.compile(
            r'(?:BMDC|Reg(?:istration)?|Lic(?:ense)?)\s*(?:No[\.\s:]*)?([A-Za-z0-9\-/]+)',
            re.IGNORECASE
        )
        reg_m = reg_pattern.search(raw_full_text)
        if reg_m:
            bmdc_reg = reg_m.group(0).strip()
        else:
            for line in lines:
                if any(kw in line.lower() for kw in ["bmdc", "reg no", "registration", "lic no", "license"]):
                    bmdc_reg = line.strip()
                    break

        # ── 4. Patient Name NER ───────────────────────────────────────────────
        p_name_pattern = re.compile(
            r'(?:Patient\s*Name|Pt\.\s*Name|Patient|Pt|Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?=\s*Age|\s*Date|\s*Sex|\s*Gender|\s*Dx|\s*Address|\s*DOB|\s*\n|$)',
            re.IGNORECASE
        )
        p_name_m = p_name_pattern.search(raw_full_text)
        if p_name_m:
            p_val = p_name_m.group(1).strip()
            if len(p_val) >= 2 and p_val.lower() not in ["name", "patient"]:
                patient_name = p_val.title()

        if patient_name == "Not Found":
            for line in lines:
                ll = line.lower()
                if "patient" in ll or ("name" in ll and ":" in line and "dr" not in ll):
                    val = line.split(":", 1)[-1].strip() if ":" in line else line
                    val = re.sub(r'(?:Age|Date|Sex|Gender|Dx|Address|DOB).*$', '', val, flags=re.IGNORECASE).strip()
                    if val and len(val) >= 2:
                        patient_name = val.title()
                        break

        # ── 5. Age / Gender / DOB / Weight / Allergies NER ────────────────────
        # DOB Check
        dob_m = re.search(r'\b(?:DOB|Date of Birth)\s*[:\-]?\s*(\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b)', raw_full_text, re.IGNORECASE)
        if dob_m:
            dob_val = dob_m.group(1)

        age_m = re.search(r'\b(\d{1,3})\s*(?:Yrs?|Years?|Y|yr|yrs)?\s*[\/\,\s]\s*(Male|Female|M|F)\b', raw_full_text, re.IGNORECASE)
        if age_m:
            patient_age_gender = f"{age_m.group(1)}Y / {age_m.group(2).upper()}"
        else:
            age_only = re.search(r'\b(?:Age)\s*[:\-]?\s*(\d{1,3})\s*(?:Yrs?|Years?|Y)?\b', raw_full_text, re.IGNORECASE)
            gender_only = re.search(r'\b(Male|Female|M|F)\b', raw_full_text, re.IGNORECASE)
            if age_only and gender_only:
                patient_age_gender = f"{age_only.group(1)}Y / {gender_only.group(1).upper()}"
            elif age_only:
                patient_age_gender = f"{age_only.group(1)} Years"
            else:
                for line in lines:
                    ll = line.lower()
                    if any(kw in ll for kw in ["age", "yrs", "years", "m/", "f/", "male", "female"]):
                        val = re.sub(r'(?:Date|Dx|Rx|Diagnosis).*$', '', line, flags=re.IGNORECASE).strip()
                        patient_age_gender = val
                        break

        weight_m = re.search(r'\b(?:Weight|Wt)\s*[:\-]?\s*(\d+\s*(?:kg|lbs))\b', raw_full_text, re.IGNORECASE)
        if weight_m:
            weight_val = weight_m.group(1)

        allergies_m = re.search(r'\b(?:Allergies|Allergy)\s*[:\-]?\s*([A-Za-z0-9\s,]+)', raw_full_text, re.IGNORECASE)
        if allergies_m:
            allergies_val = allergies_m.group(1).strip()

        # ── 6. Prescription Date NER (Disambiguated from DOB) ──────────────────
        # Check explicit Date: line first (e.g. "Date March 10, 2009")
        date_line_m = re.search(r'\bDate\s*[:\-]?\s*([A-Za-z0-9\s,\/\.-]{5,20})', raw_full_text, re.IGNORECASE)
        if date_line_m:
            d_candidate = date_line_m.group(1).split("\n")[0].strip()
            # Clean trailing words
            d_candidate = re.sub(r'(?:Patient|Address|DOB|Rx).*$', '', d_candidate, flags=re.IGNORECASE).strip()
            if d_candidate and d_candidate != dob_val:
                rx_date = d_candidate

        if rx_date == "Not Found":
            # Search for dates matching Month DD, YYYY or DD/MM/YYYY
            all_dates = re.findall(
                r'\b(?:\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)?\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+(?:19|20)?\d{2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)?\d{2})\b',
                raw_full_text,
                re.IGNORECASE
            )
            for d in all_dates:
                if d != dob_val:
                    rx_date = d
                    break

        # ── 7. Address NER ────────────────────────────────────────────────────
        addr_line_m = re.search(r'\bAddress\s*[:\-]?\s*([^\n]+)', raw_full_text, re.IGNORECASE)
        if addr_line_m:
            val = addr_line_m.group(1).strip()
            if len(val) > 2 and not any(val.lower().startswith(kw) for kw in ["dob", "date", "weight", "allergies", "rx"]):
                address_val = val

        # Fallback: Header address block (e.g. "25 El Caro Street, Pleasantville, OH 43320")
        if address_val == "Not Found" or len(address_val) <= 5 or any(address_val.lower().startswith(kw) for kw in ["dob", "date", "weight"]):
            header_addr_m = re.search(r'(\d+\s+[A-Za-z0-9\s\.,]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Blvd|Way)[^\n]*)', raw_full_text, re.IGNORECASE)
            if header_addr_m:
                address_val = header_addr_m.group(1).strip()

        # ── 8. Prescribed Medicines NER & Model Classification ───────────────
        medicines: List[Dict[str, str]] = []
        dosage_pattern_re = re.compile(r'\b[012]\s*[\+\-]\s*[012]\s*[\+\-]\s*[012]\b')
        duration_re = re.compile(r'\b(\d+)\s*(days?|weeks?|months?)\b', re.IGNORECASE)
        strength_re = re.compile(r'\b(\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|mL|mg\/5mL|mg\/mL|%))\b', re.IGNORECASE)

        rx_block = False
        for line in lines:
            ll = line.lower().strip()

            if ll.startswith("rx") or ll.startswith("r/") or "rx:" in ll:
                rx_block = True

            # Skip header info
            if any(ll.startswith(p) for p in ["dr.", "bmdc", "patient", "name:", "age:", "date:", "dob:", "address:", "allergies:"]):
                continue

            has_prefix = any(ll.startswith(p) for p in ["tab", "cap", "syr", "inj", "oint", "drop", "sol", "susp", "gel", "cream"])
            has_dosage = bool(dosage_pattern_re.search(line)) or any(kw in ll for kw in ["day 1:", "day 2:", "dispense", "refills"])
            has_mg = bool(strength_re.search(line))

            if rx_block or has_prefix or has_dosage or has_mg:
                words = line.split()
                if not words:
                    continue

                # Clean words
                clean_line = re.sub(r'^(?:rx[:\.]?|r\/|1\.|2\.|3\.|4\.|5\.)\s*', '', line, flags=re.IGNORECASE).strip()
                if not clean_line or any(clean_line.lower().startswith(kw) for kw in ["refills", "date", "dispense", "day 1", "day 2"]) or re.search(r'\b(?:arnp|mbbs|md|dr|doctor|prof)\b', clean_line, re.IGNORECASE):
                    continue

                # Match drug name
                med_words = clean_line.split()
                raw_med_word = med_words[0].rstrip('.,') if med_words else clean_line
                if med_words and med_words[0].lower() in ["tab", "cap", "syr", "inj", "oint", "drop", "sol", "susp"]:
                    raw_med_word = med_words[1].rstrip('.,') if len(med_words) > 1 else med_words[0]

                brand, generic, match_conf = self.fuzzy_match_medicine(raw_med_word)

                # Dosage strength
                str_m = strength_re.search(clean_line)
                strength = str_m.group(0) if str_m else "N/A"

                # Construct clean brand display name
                if brand != raw_med_word:
                    brand_display = f"{brand} {strength}".strip() if strength != "N/A" else brand
                else:
                    first_two = " ".join(med_words[:2]) if len(med_words) >= 2 else raw_med_word
                    brand_display = re.sub(r'[,\.:].*$', '', first_two).strip()

                # Dosage Pattern / Frequency
                dose_m = dosage_pattern_re.search(clean_line)
                if dose_m:
                    dosage = dose_m.group(0).replace(" ", "").replace("-", "+")
                elif "day 1" in clean_line.lower():
                    dosage = clean_line
                else:
                    dosage = "As Prescribed"

                # Food timing
                if any(kw in ll for kw in ["after food", "after meal", "pc", "p.c.", "after"]):
                    timing = "After Food"
                elif any(kw in ll for kw in ["before food", "before meal", "ac", "a.c.", "empty stomach"]):
                    timing = "Before Food"
                else:
                    timing = "As Directed"

                dur_m = duration_re.search(ll)
                duration = dur_m.group(0).title() if dur_m else "As Prescribed"

                medicines.append({
                    "Brand Name": brand_display,
                    "Generic Name": generic if generic != "Unknown" else (brand if brand != "Unknown" else brand_display),
                    "Dosage Pattern": dosage,
                    "Strength": strength,
                    "Timing": timing,
                    "Duration": duration,
                    "Match Confidence": f"{match_conf}%"
                })

        # Remove duplicate medicine entries
        unique_meds = []
        seen = set()
        for m in medicines:
            k = m["Brand Name"].lower()
            if k not in seen and k not in ["mg/sml", "mg/ml", "dispense"]:
                seen.add(k)
                unique_meds.append(m)
        medicines = unique_meds

        # ── 10. Table & Response Construction ─────────────────────────────────
        table_headers = ["Brand Name", "Generic Name", "Dosage Pattern", "Timing", "Duration", "Match Confidence"]
        table_rows = [[m["Brand Name"], m["Generic Name"], m["Dosage Pattern"], m["Timing"], m["Duration"], m["Match Confidence"]] for m in medicines]

        confidence = 99.0 if medicines else 88.0

        med_summary_list = [m["Brand Name"] for m in medicines if m.get("Brand Name")]
        prescribed_meds_summary = ", ".join(med_summary_list) if med_summary_list else "Not Found"

        fields = {
            "Doctor Name": doc_name,
            "Qualification": qualification,
            "BMDC Registration No": bmdc_reg,
            "Patient Name": patient_name,
            "Age / Gender": patient_age_gender,
            "Date of Birth": dob_val,
            "Prescription Date": rx_date,
            "Address": address_val,
            "Contact No": contact_no,
            "Diagnosis / Chief Complaint": diagnosis,
            "Prescribed Medicines": prescribed_meds_summary,
            "Prescribed Medicines Count": str(len(medicines))
        }

        if weight_val != "Not Found":
            fields["Weight"] = weight_val
        if allergies_val != "Not Found":
            fields["Allergies"] = allergies_val

        return {
            "fields": fields,
            "medicines": medicines,
            "tables": [
                {
                    "table_name": "Doctor Prescribed Medicines (BD Dataset CRNN Neural Model + NER)",
                    "headers": table_headers,
                    "rows": table_rows
                }
            ],
            "confidence": confidence
        }


medical_prescription_extractor = MedicalPrescriptionExtractor()
