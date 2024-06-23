-- Step 1: Filter diagnosis to I50% (Heart failure patients only)
CREATE OR REPLACE TABLE `mimic_ed.1_hf_diagnosis` AS
SELECT
  subject_id,
  stay_id,
  icd_code,
  icd_version,
  icd_title
FROM `physionet-data.mimiciv_ed.diagnosis`
WHERE icd_code LIKE 'I50%';

-- Count rows for step 1
CREATE OR REPLACE TABLE `mimic_ed.count_1_hf_diagnosis` AS
SELECT
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.1_hf_diagnosis`;

-- Step 2: Join edstays
CREATE OR REPLACE TABLE `mimic_ed.2_hf_edstays` AS
SELECT
    d.*,
    e.hadm_id,
    -- Rename gender
    CASE
        WHEN e.gender = 'M' THEN 'Male'
        WHEN e.gender = 'F' THEN 'Female'
        ELSE NULL
    END AS gender,
    -- Group race
    CASE 
        WHEN race IN ('WHITE', 'WHITE - OTHER EUROPEAN', 'WHITE - RUSSIAN', 'WHITE - EASTERN EUROPEAN', 'WHITE - BRAZILIAN') THEN 'White'
        WHEN race IN ('BLACK/AFRICAN AMERICAN', 'BLACK/AFRICAN', 'BLACK/CARIBBEAN ISLAND', 'BLACK/CAPE VERDEAN') THEN 'Black/African American'
        WHEN race IN ('ASIAN - CHINESE', 'ASIAN', 'ASIAN - SOUTH EAST ASIAN', 'ASIAN - ASIAN INDIAN') THEN 'Asian'
        WHEN race LIKE 'HISPANIC/LATINO%' OR race IN ('SOUTH AMERICAN', 'PORTUGUESE') THEN 'Hispanic/Latino'
        WHEN race IN ('AMERICAN INDIAN/ALASKA NATIVE', 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER') THEN 'Native/Indigenous'
        ELSE 'Other/Unknown'
    END AS race,
    e.arrival_transport,
    e.disposition
FROM
    `mimic_ed.1_hf_diagnosis` AS d
LEFT JOIN 
    `physionet-data.mimiciv_ed.edstays` AS e
ON 
    d.stay_id = e.stay_id AND d.subject_id = e.subject_id
WHERE
    e.disposition IN ('HOME', 'ADMITTED');

-- Count rows for step 2
CREATE OR REPLACE TABLE `mimic_ed.count_2_hf_edstays` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.2_hf_edstays`
GROUP BY
    disposition;

-- Step 3: Join triage table
CREATE OR REPLACE TABLE `mimic_ed.3_hf_triage` AS
SELECT
    e.*,
    t.temperature AS triage_temperature,
    t.heartrate AS triage_heartrate,
    t.resprate AS triage_resprate,
    t.o2sat AS triage_o2sat,
    t.sbp AS triage_sbp,
    t.dbp AS triage_dbp,
    t.pain AS triage_pain,
    t.acuity AS triage_acuity,
    t.chiefcomplaint AS triage_chiefcomplaint
FROM
    `mimic_ed.2_hf_edstays` AS e
INNER JOIN
    `physionet-data.mimiciv_ed.triage` AS t
ON
    e.stay_id = t.stay_id AND e.subject_id = t.subject_id;

-- Count rows for step 3
CREATE OR REPLACE TABLE `mimic_ed.count_3_hf_triage` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.3_hf_triage`
GROUP BY
    disposition;

-- Step 4: Prep vital signs table
CREATE OR REPLACE TABLE `mimic_ed.temp_hf_latest_vitalsign` AS
WITH vitals_with_count AS (
    SELECT
        v.subject_id,
        v.stay_id,
        v.temperature,
        v.heartrate,
        v.resprate,
        v.o2sat,
        v.sbp,
        v.dbp,
        v.rhythm,
        v.pain,
        v.charttime,
        -- Count non-null values in the specified columns
        (CASE WHEN v.temperature IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.heartrate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.resprate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.o2sat IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.sbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.dbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.rhythm IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN v.pain IS NOT NULL THEN 1 ELSE 0 END) AS non_null_count
    FROM
        `physionet-data.mimiciv_ed.vitalsign` AS v
    INNER JOIN
        `mimic_ed.1_hf_diagnosis` AS d
    ON
        v.subject_id = d.subject_id AND v.stay_id = d.stay_id
)
-- Select the row with the highest non_null_count and the latest charttime
SELECT
    subject_id,
    stay_id,
    temperature,
    heartrate,
    resprate,
    o2sat,
    sbp,
    dbp,
    rhythm,
    pain
FROM (
    SELECT
        subject_id,
        stay_id,
        temperature,
        heartrate,
        resprate,
        o2sat,
        sbp,
        dbp,
        rhythm,
        pain,
        charttime,
        non_null_count,
        ROW_NUMBER() OVER (PARTITION BY subject_id, stay_id ORDER BY non_null_count DESC, charttime DESC) AS rn
    FROM
        vitals_with_count
)
WHERE rn = 1;

-- Step 5: Join vital signs table
CREATE OR REPLACE TABLE `mimic_ed.5_hf_vitalsign` AS
SELECT
    t.*,
    v.temperature AS vitals_temperature,
    v.heartrate AS vitals_heartrate,
    v.resprate AS vitals_resprate,
    v.o2sat AS vitals_o2sat,
    v.sbp AS vitals_sbp,
    v.dbp AS vitals_dbp,
    v.rhythm AS vitals_rhythm,
    v.pain AS vitals_pain
FROM
    `mimic_ed.3_hf_triage` AS t
LEFT JOIN
    `mimic_ed.temp_hf_latest_vitalsign` AS v
ON
    t.stay_id = v.stay_id AND t.subject_id = v.subject_id;

-- Count rows for step 5
CREATE OR REPLACE TABLE `mimic_ed.count_5_hf_vitalsign` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.5_hf_vitalsign`
GROUP BY
    disposition;

-- Step 6: Join additional data from hosp module (patients table)
CREATE OR REPLACE TABLE `mimic_ed.6_hf_patients` AS
SELECT
    v.*,
    p.anchor_age AS age,
    CASE WHEN p.dod IS NOT NULL THEN 1 ELSE 0 END AS hosp_died_within_year
FROM `mimic_ed.5_hf_vitalsign` AS v
LEFT JOIN `physionet-data.mimiciv_hosp.patients` AS p
ON v.subject_id = p.subject_id;

-- Count rows for step 6
CREATE OR REPLACE TABLE `mimic_ed.count_6_hf_patients` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.6_hf_patients`
GROUP BY
    disposition;

-- Step 7: Join additional data from hosp module (admissions table)
CREATE OR REPLACE TABLE `mimic_ed.7_hf_admissions` AS
SELECT
    a.*,
    ad.discharge_location AS hosp_discharge_location,
    ad.insurance AS insurance,
    ad.marital_status AS marital_status
FROM `mimic_ed.6_hf_patients` AS a
LEFT JOIN `physionet-data.mimiciv_hosp.admissions` AS ad
ON a.subject_id = ad.subject_id AND a.hadm_id = ad.hadm_id;

-- Count rows for step 7
CREATE OR REPLACE TABLE `mimic_ed.count_7_hf_admissions` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.7_hf_admissions`
GROUP BY
    disposition;

-- Step 8: Process and join medications table
-- Prepare cleaned medrecon table
CREATE OR REPLACE TABLE `mimic_ed.temp_hf_cleaned_medrecon` AS
WITH filtered_medrecon AS (
    SELECT
        m.subject_id,
        m.stay_id,
        m.ndc,
        m.name,
        m.gsn,
        m.etc_rn,
        m.etccode,
        m.etcdescription
    FROM
        `physionet-data.mimiciv_ed.medrecon` AS m
    INNER JOIN
        `mimic_ed.1_hf_diagnosis` AS d
    ON
        m.subject_id = d.subject_id AND m.stay_id = d.stay_id
),
-- Get Distinct Combinations of `ndc` and `name` with Counts
ndc_name_counts AS (
    SELECT
        ndc,
        name,
        COUNT(*) AS name_count
    FROM
        filtered_medrecon
    GROUP BY
        ndc, name
),
-- Select the Name with the Highest Count for Each `ndc`
majority_ndc_name AS (
    SELECT
        ndc,
        name,
        name_count,
        ROW_NUMBER() OVER (PARTITION BY ndc ORDER BY name_count DESC, name) AS rn
    FROM
        ndc_name_counts
)
-- Rejoin to the Medication Table
SELECT
    f.subject_id,
    f.stay_id,
    f.ndc,
    c.name,
    f.gsn,
    f.etccode,
    f.etcdescription
FROM
    filtered_medrecon AS f
LEFT JOIN
    majority_ndc_name AS c
ON
    f.ndc = c.ndc
WHERE
    c.rn = 1 AND etccode IN (
        '00000238', '00000239', '00000224', '00006043', '00000214', '00000242', '00006569', '00000225',
        '00006578', '00000206', '00005917', '00000221', '00002734', '00002534', '00000218', '00000219',
        '00000220', '00000189', '00006397', '00005887', '00000264', '00000265', '00002747', '00000268',
        '00006783', '00005678', '00003466', '00000767', '00005784', '00005845', '00002530', '00002527',
        '00002529', '00004610', '00004609', '00004611', '00000202', '00002730', '00003065', '00003064',
        '00002718', '00000203', '00002722', '00006182', '00005658', '00005659', '00000249', '00000250',
        '00000253', '00002713', '00000254', '00000280', '00000281', '00000804', '00006183', '00000805',
        '00006263', '00005796', '00000824', '00000822', '00005843', '00005795'
    );

SELECT
    name,
    count(stay_id)
FROM
    `double-insight-425316-k4.mimic_ed.temp_hf_cleaned_medrecon`
GROUP BY
    name
ORDER BY
    name;

-- Step 1: Create the mapping table with medication standardization
CREATE OR REPLACE TABLE `mimic_ed.medication_mapping` AS
WITH mapping AS (
  SELECT 'Avalide' AS original_name, 'Avalide' AS standardized_name UNION ALL
  SELECT 'Benicar', 'Benicar' UNION ALL
  SELECT 'Brilinta', 'Brilinta' UNION ALL
  SELECT 'Cardizem LA', 'Cardizem LA' UNION ALL
  SELECT 'Cialis', 'Cialis' UNION ALL
  SELECT 'DILT-XR', 'Diltiazem' UNION ALL
  SELECT 'Eliquis', 'Eliquis' UNION ALL
  SELECT 'Entresto', 'Entresto' UNION ALL
  SELECT 'Farxiga', 'Farxiga' UNION ALL
  SELECT 'Fish Oil', 'Fish Oil' UNION ALL
  SELECT 'Hyzaar', 'Losartan-Hydrochlorothiazide' UNION ALL
  SELECT 'Invokana', 'Invokana' UNION ALL
  SELECT 'Jardiance', 'Jardiance' UNION ALL
  SELECT 'Lescol', 'Fluvastatin' UNION ALL
  SELECT 'Livalo', 'Pitavastatin' UNION ALL
  SELECT 'Nitro-Bid', 'Nitroglycerin' UNION ALL
  SELECT 'Nitrolingual', 'Nitroglycerin' UNION ALL
  SELECT 'Omega 3 Fish Oil', 'Fish Oil' UNION ALL
  SELECT 'Omega-3', 'Fish Oil' UNION ALL
  SELECT 'Omega-3 Fatty Acids-Fish Oil', 'Fish Oil' UNION ALL
  SELECT 'Omega-3 Fish Oil', 'Fish Oil' UNION ALL
  SELECT 'Procardia', 'Nifedipine' UNION ALL
  SELECT 'Questran', 'Cholestyramine' UNION ALL
  SELECT 'Quinapril', 'Quinapril' UNION ALL
  SELECT 'Stimate', 'Desmopressin' UNION ALL
  SELECT 'Trulicity', 'Dulaglutide' UNION ALL
  SELECT 'Viagra', 'Sildenafil' UNION ALL
  SELECT 'WelChol', 'Colesevelam' UNION ALL
  SELECT 'Xarelto', 'Rivaroxaban' UNION ALL
  SELECT 'acebutolol', 'Acebutolol' UNION ALL
  SELECT 'acetazolamide', 'Acetazolamide' UNION ALL
  SELECT 'alirocumab', 'Praluent' UNION ALL
  SELECT 'alprostadil [Edex]', 'Alprostadil' UNION ALL
  SELECT 'amiloride', 'Amiloride' UNION ALL
  SELECT 'amiodarone', 'Amiodarone' UNION ALL
  SELECT 'amlodipine', 'Amlodipine' UNION ALL
  SELECT 'amlodipine-atorvastatin', 'Caduet' UNION ALL
  SELECT 'amlodipine-benazepril', 'Lotrel' UNION ALL
  SELECT 'amlodipine-benazepril [Lotrel]', 'Lotrel' UNION ALL
  SELECT 'aspirin', 'Aspirin' UNION ALL
  SELECT 'aspirin-dipyridamole [Aggrenox]', 'Aggrenox' UNION ALL
  SELECT 'atenolol', 'Atenolol' UNION ALL
  SELECT 'atenolol-chlorthalidone', 'Tenoretic' UNION ALL
  SELECT 'atorvastatin', 'Atorvastatin' UNION ALL
  SELECT 'benazepril', 'Benazepril' UNION ALL
  SELECT 'bisoprolol fumarate', 'Bisoprolol' UNION ALL
  SELECT 'bumetanide', 'Bumetanide' UNION ALL
  SELECT 'candesartan', 'Candesartan' UNION ALL
  SELECT 'captopril', 'Captopril' UNION ALL
  SELECT 'carvedilol', 'Carvedilol' UNION ALL
  SELECT 'carvedilol phosphate [Coreg CR]', 'Carvedilol' UNION ALL
  SELECT 'chlorthalidone', 'Chlorthalidone' UNION ALL
  SELECT 'cholestyramine-aspartame [Cholestyramine Light]', 'Cholestyramine' UNION ALL
  SELECT 'cilostazol', 'Cilostazol' UNION ALL
  SELECT 'clonidine', 'Clonidine' UNION ALL
  SELECT 'clonidine HCl', 'Clonidine' UNION ALL
  SELECT 'clopidogrel', 'Clopidogrel' UNION ALL
  SELECT 'colestipol', 'Colestipol' UNION ALL
  SELECT 'desmopressin', 'Desmopressin' UNION ALL
  SELECT 'digoxin', 'Digoxin' UNION ALL
  SELECT 'diltiazem HCl', 'Diltiazem' UNION ALL
  SELECT 'diltiazem HCl [Cardizem LA]', 'Diltiazem' UNION ALL
  SELECT 'diltiazem HCl [DILT-XR]', 'Diltiazem' UNION ALL
  SELECT 'diltiazem HCl [Matzim LA]', 'Diltiazem' UNION ALL
  SELECT 'dipyridamole', 'Dipyridamole' UNION ALL
  SELECT 'dobutamine', 'Dobutamine' UNION ALL
  SELECT 'dobutamine in D5W', 'Dobutamine' UNION ALL
  SELECT 'dofetilide', 'Dofetilide' UNION ALL
  SELECT 'dofetilide [Tikosyn]', 'Dofetilide' UNION ALL
  SELECT 'dronedarone [Multaq]', 'Dronedarone' UNION ALL
  SELECT 'enalapril maleate', 'Enalapril' UNION ALL
  SELECT 'enalapril-hydrochlorothiazide', 'Vaseretic' UNION ALL
  SELECT 'enoxaparin', 'Enoxaparin' UNION ALL
  SELECT 'enoxaparin [Lovenox]', 'Enoxaparin' UNION ALL
  SELECT 'epinephrine [EpiPen]', 'Epinephrine' UNION ALL
  SELECT 'eplerenone', 'Eplerenone' UNION ALL
  SELECT 'ethacrynic acid', 'Ethacrynic Acid' UNION ALL
  SELECT 'ezetimibe [Zetia]', 'Ezetimibe' UNION ALL
  SELECT 'ezetimibe-simvastatin', 'Vytorin' UNION ALL
  SELECT 'felodipine', 'Felodipine' UNION ALL
  SELECT 'fenofibrate', 'Fenofibrate' UNION ALL
  SELECT 'fenofibrate micronized', 'Fenofibrate' UNION ALL
  SELECT 'fenofibrate nanocrystallized', 'Fenofibrate' UNION ALL
  SELECT 'fenofibrate nanocrystallized [Tricor]', 'Fenofibrate' UNION ALL
  SELECT 'fenofibric acid (choline)', 'Fenofibrate' UNION ALL
  SELECT 'fish oil-dha-epa', 'Fish Oil' UNION ALL
  SELECT 'fish oil-omega-3-vit C-vit E', 'Fish Oil' UNION ALL
  SELECT 'flecainide', 'Flecainide' UNION ALL
  SELECT 'fluvastatin', 'Lescol' UNION ALL
  SELECT 'fondaparinux', 'Arixtra' UNION ALL
  SELECT 'fosinopril', 'Fosinopril' UNION ALL
  SELECT 'fsh-flx-prm-blkbor-om 3,6,9 #5 [Omega 3-6-9 Fatty Acids]', 'Omega 3-6-9 Fatty Acids' UNION ALL
  SELECT 'furosemide', 'Furosemide' UNION ALL
  SELECT 'gemfibrozil', 'Gemfibrozil' UNION ALL
  SELECT 'guanfacine', 'Guanfacine' UNION ALL
  SELECT 'heparin (porcine)', 'Heparin' UNION ALL
  SELECT 'heparin (porcine) in 0.9% NaCl [Heparin Flush]', 'Heparin' UNION ALL
  SELECT 'heparin flush(porcine)-0.9NaCl', 'Heparin' UNION ALL
  SELECT 'heparin lock flush (porcine)', 'Heparin' UNION ALL
  SELECT 'heparin, porcine (PF)', 'Heparin' UNION ALL
  SELECT 'hydralazine', 'Hydralazine' UNION ALL
  SELECT 'hydrochlorothiazide', 'Hydrochlorothiazide' UNION ALL
  SELECT 'hydrochlorothiazide (bulk)', 'Hydrochlorothiazide' UNION ALL
  SELECT 'indapamide', 'Indapamide' UNION ALL
  SELECT 'irbesartan', 'Irbesartan' UNION ALL
  SELECT 'irbesartan [Avapro]', 'Irbesartan' UNION ALL
  SELECT 'irbesartan-hydrochlorothiazide', 'Avalide' UNION ALL
  SELECT 'isosorbide dinitrate', 'Isosorbide Dinitrate' UNION ALL
  SELECT 'isosorbide mononitrate', 'Isosorbide Mononitrate' UNION ALL
  SELECT 'krill-om3-dha-epa-om6-lip-astx [Krill Oil (Omega 3 & 6)]', 'Krill Oil' UNION ALL
  SELECT 'labetalol', 'Labetalol' UNION ALL
  SELECT 'lidocaine HCl', 'Lidocaine' UNION ALL
  SELECT 'liraglutide [Victoza 2-Pak]', 'Victoza' UNION ALL
  SELECT 'lisinopril', 'Lisinopril' UNION ALL
  SELECT 'lisinopril-hydrochlorothiazide', 'Lisinopril-Hydrochlorothiazide' UNION ALL
  SELECT 'losartan', 'Losartan' UNION ALL
  SELECT 'losartan-hydrochlorothiazide', 'Losartan-Hydrochlorothiazide' UNION ALL
  SELECT 'lovastatin', 'Lovastatin' UNION ALL
  SELECT 'lovastatin [Altoprev]', 'Lovastatin' UNION ALL
  SELECT 'methyldopa', 'Methyldopa' UNION ALL
  SELECT 'metolazone', 'Metolazone' UNION ALL
  SELECT 'metoprolol succinate', 'Metoprolol' UNION ALL
  SELECT 'metoprolol tartrate', 'Metoprolol' UNION ALL
  SELECT 'mexiletine', 'Mexiletine' UNION ALL
  SELECT 'midodrine', 'Midodrine' UNION ALL
  SELECT 'milrinone', 'Milrinone' UNION ALL
  SELECT 'milrinone in 5 % dextrose', 'Milrinone' UNION ALL
  SELECT 'minoxidil', 'Minoxidil' UNION ALL
  SELECT 'moexipril', 'Moexipril' UNION ALL
  SELECT 'moexipril-hydrochlorothiazide', 'Moexipril-Hydrochlorothiazide' UNION ALL
  SELECT 'nadolol', 'Nadolol' UNION ALL
  SELECT 'nebivolol [Bystolic]', 'Nebivolol' UNION ALL
  SELECT 'niacin [Niaspan Extended-Release]', 'Niaspan' UNION ALL
  SELECT 'nifedipine', 'Nifedipine' UNION ALL
  SELECT 'nitroglycerin', 'Nitroglycerin' UNION ALL
  SELECT 'nitroglycerin [Nitrostat]', 'Nitroglycerin' UNION ALL
  SELECT 'olmesartan', 'Olmesartan' UNION ALL
  SELECT 'omega 3-dha-epa-fish oil', 'Fish Oil' UNION ALL
  SELECT 'omega 3-dha-epa-fish oil [Fish Oil]', 'Fish Oil' UNION ALL
  SELECT 'omega-3 acid ethyl esters', 'Omega-3 Acid Ethyl Esters' UNION ALL
  SELECT 'omega-3 fatty acids', 'Omega-3 Fatty Acids' UNION ALL
  SELECT 'omega-3 fatty acids-fish oil', 'Fish Oil' UNION ALL
  SELECT 'omega-3 fatty acids-fish oil [Fish Oil Extra Strength]', 'Fish Oil' UNION ALL
  SELECT 'omega-3 fatty acids-fish oil [Fish Oil]', 'Fish Oil' UNION ALL
  SELECT 'prasugrel [Effient]', 'Prasugrel' UNION ALL
  SELECT 'pravastatin', 'Pravastatin' UNION ALL
  SELECT 'propranolol', 'Propranolol' UNION ALL
  SELECT 'quinapril', 'Quinapril' UNION ALL
  SELECT 'quinidine gluconate', 'Quinidine' UNION ALL
  SELECT 'ramipril', 'Ramipril' UNION ALL
  SELECT 'ranolazine [Ranexa]', 'Ranolazine' UNION ALL
  SELECT 'rivaroxaban', 'Rivaroxaban' UNION ALL
  SELECT 'rosuvastatin', 'Rosuvastatin' UNION ALL
  SELECT 'rosuvastatin [Crestor]', 'Rosuvastatin' UNION ALL
  SELECT 'sildenafil [Viagra]', 'Sildenafil' UNION ALL
  SELECT 'simvastatin', 'Simvastatin' UNION ALL
  SELECT 'sotalol', 'Sotalol' UNION ALL
  SELECT 'spironolacton-hydrochlorothiaz', 'Spironolactone-Hydrochlorothiazide' UNION ALL
  SELECT 'spironolactone', 'Spironolactone' UNION ALL
  SELECT 'tadalafil', 'Tadalafil' UNION ALL
  SELECT 'tadalafil [Cialis]', 'Tadalafil' UNION ALL
  SELECT 'telmisartan', 'Telmisartan' UNION ALL
  SELECT 'telmisartan [Micardis]', 'Telmisartan' UNION ALL
  SELECT 'torsemide', 'Torsemide' UNION ALL
  SELECT 'trandolapril', 'Trandolapril' UNION ALL
  SELECT 'triamterene [Dyrenium]', 'Triamterene' UNION ALL
  SELECT 'triamterene-hydrochlorothiazid', 'Triamterene-Hydrochlorothiazide' UNION ALL
  SELECT 'valsartan', 'Valsartan' UNION ALL
  SELECT 'valsartan-hydrochlorothiazide', 'Valsartan-Hydrochlorothiazide' UNION ALL
  SELECT 'valsartan-hydrochlorothiazide [Diovan HCT]', 'Valsartan-Hydrochlorothiazide' UNION ALL
  SELECT 'vardenafil [Levitra]', 'Vardenafil' UNION ALL
  SELECT 'verapamil', 'Verapamil' UNION ALL
  SELECT 'vit C-vit E-lutein-min-om-3 [Ocuvite]', 'Multivitamins'
)
SELECT * FROM mapping;

-- Apply the Mapping to Standardize Medication Names
CREATE OR REPLACE TABLE `mimic_ed.temp_hf_standardized_medrecon` AS
SELECT
    r.subject_id,
    r.stay_id,
    r.ndc,
    COALESCE(m.standardized_name, r.name) AS standardized_name,  -- Replace with standardized name if available
    r.gsn,
    r.etccode,
    r.etcdescription
FROM
    `mimic_ed.temp_hf_cleaned_medrecon` r
LEFT JOIN
    `mimic_ed.medication_mapping` m
ON
    r.name = m.original_name;

-- Aggregate Standardized Medication Names
CREATE OR REPLACE TABLE `mimic_ed.temp_hf_aggregated_medrecon` AS
SELECT
    subject_id,
    stay_id,
    STRING_AGG(standardized_name, ', ') AS all_meds
FROM
    `mimic_ed.temp_hf_standardized_medrecon`
GROUP BY
    subject_id,
    stay_id;

-- Final join with admissions data
CREATE OR REPLACE TABLE `mimic_ed.8_hf_meds` AS
SELECT
    a.*,
    m.all_meds
FROM
    `mimic_ed.7_hf_admissions` AS a
LEFT JOIN
    `mimic_ed.temp_hf_aggregated_medrecon` AS m
ON
    a.subject_id = m.subject_id AND a.stay_id = m.stay_id;

-- Count rows for step 8
CREATE OR REPLACE TABLE `mimic_ed.count_8_hf_meds` AS
SELECT
    disposition,
    COUNT(stay_id) AS count_stay_id
FROM
    `mimic_ed.8_hf_meds`
GROUP BY
    disposition;

-- Step 9. Filter out those who died in hospital
SELECT
    disposition,
    count(stay_id) as count_stay_id
FROM
    `mimic_ed.8_hf_meds`
WHERE
    hosp_discharge_location = 'DIED'
GROUP BY
    disposition;
    
-- Create a filtered table excluding only the 'DIED' records, and keeping NULLs
CREATE OR REPLACE TABLE `mimic_ed.9_hf_alive` AS
SELECT
    *
FROM
    `mimic_ed.8_hf_meds`
WHERE
    hosp_discharge_location IS NULL OR hosp_discharge_location <> 'DIED';

-- Count rows for step 9
CREATE OR REPLACE TABLE `mimic_ed.count_9_hf_alive` AS
SELECT
    disposition,
    count(stay_id) AS count_stay_id
FROM
    `mimic_ed.9_hf_alive`
GROUP BY
    disposition;

-- Step 10: Consolidate and Process Vitals Data
CREATE OR REPLACE TABLE `mimic_ed.10_hf_final` AS
WITH temp_vitals_processed AS (
    SELECT
        *,
        -- Count non-null fields in triage columns
        (CASE WHEN triage_temperature IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_heartrate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_resprate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_o2sat IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_sbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_dbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN triage_pain IS NOT NULL THEN 1 ELSE 0 END) AS triage_non_null_count,

        -- Count non-null fields in vitals columns
        (CASE WHEN vitals_temperature IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_heartrate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_resprate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_o2sat IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_sbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_dbp IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN vitals_pain IS NOT NULL THEN 1 ELSE 0 END) AS vitals_non_null_count
    FROM
        `mimic_ed.9_hf_alive`
),
cleaned_vitals AS (
    SELECT
        -- Identifiers and Key References
        subject_id,
        stay_id,
        hadm_id,

        -- Demographics
        gender,
        INITCAP(race) as race,
        age,
        INITCAP(insurance) as insurance,
        INITCAP(marital_status) as marital_status,

        -- Diagnosis Information
        icd_code,
        icd_version,
        icd_title,

        -- Symptoms
        triage_chiefcomplaint AS chiefcomplaint,
        triage_acuity AS acuity,

        -- Replace vitals values with triage values if triage has more non-null counts
        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_temperature
            ELSE vitals_temperature
        END AS vitals_temperature,

        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_heartrate
            ELSE vitals_heartrate
        END AS vitals_heartrate,

        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_resprate
            ELSE vitals_resprate
        END AS vitals_resprate,

        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_o2sat
            ELSE vitals_o2sat
        END AS vitals_o2sat,

        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_sbp
            ELSE vitals_sbp
        END AS vitals_sbp,

        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN triage_dbp
            ELSE vitals_dbp
        END AS vitals_dbp,

        -- Clean up pain to be 0-10 scale
        CASE
            WHEN vitals_pain NOT IN ('0','1','2','3','4','5','6','7','8','9','10')
            THEN NULL
            ELSE CAST(vitals_pain AS INT64)
        END AS vitals_pain,

        -- Standardize vitals_rhythm values
        CASE
            WHEN vitals_rhythm IN ('sr', 'SR', 'Sinus Rhythm', 'Normal Sinus Rhythm', 'nsr', 'NSR', 'SR BBB', 'sr with many pvc') THEN 'Sinus Rhythm'
            WHEN vitals_rhythm IN ('Sinus Tachycardia') THEN 'Sinus Tachycardia'
            WHEN vitals_rhythm IN ('Atrial Fibrillation', 'AFib', 'afib', 'aflutter', 'af', 'A-fib, freq PVC\'s') THEN 'Atrial Fibrillation'
            WHEN vitals_rhythm IN ('Sinus Bradycardia') THEN 'Sinus Bradycardia'
            WHEN vitals_rhythm IN ('Paced Rhythm', 'paced', 'v-paced', 'AV paced', '100%AV Paced') THEN 'Paced Rhythm'
            WHEN vitals_rhythm IN ('Bigeminy') THEN 'Bigeminy'
            WHEN vitals_rhythm IN ('irreg', 'irregular') THEN 'Irregular'
            ELSE NULL
        END AS vitals_rhythm,

        -- Indicate source of the final values
        CASE 
            WHEN triage_non_null_count > vitals_non_null_count THEN 'Triage'
            ELSE 'Vitals'
        END AS vitals_source,

        -- Outcome
        INITCAP(arrival_transport) AS ed_arrival_transport,
        INITCAP(disposition) AS ed_disposition,
        INITCAP(hosp_discharge_location) AS hosp_discharge_location,
        hosp_died_within_year AS died_within_year,

        -- Medications
        all_meds
    FROM
        temp_vitals_processed
)

SELECT * FROM cleaned_vitals
WHERE
    chiefcomplaint IS NOT NULL AND
    acuity IS NOT NULL AND
    vitals_temperature IS NOT NULL AND
    vitals_heartrate IS NOT NULL AND
    vitals_resprate IS NOT NULL AND
    vitals_o2sat IS NOT NULL AND
    vitals_sbp IS NOT NULL AND
    vitals_dbp IS NOT NULL AND
    vitals_pain IS NOT NULL AND
    all_meds IS NOT NULL AND
    vitals_temperature != 33.3 AND
    vitals_sbp != 3 AND
    vitals_dbp != 548 AND
    vitals_o2sat != 10;

-- Count outcomes of the final step
CREATE OR REPLACE TABLE `mimic_ed.count_10_hf_final` AS
SELECT
    ed_disposition,
    count(stay_id) AS count_stay_id
FROM
    `mimic_ed.10_hf_final`
GROUP BY
    ed_disposition;

-- Step 11. Add weight and height data
-- Use ROW_NUMBER() to get the latest entries per subject_id and measurement
CREATE OR REPLACE TABLE `mimic_ed.temp_height_weight` AS
WITH ranked_results AS (
    SELECT
        subject_id,
        chartdate,
        seq_num,
        result_name,
        result_value,
        ROW_NUMBER() OVER (
            PARTITION BY subject_id, result_name
            ORDER BY chartdate DESC, seq_num DESC
        ) AS rn
    FROM
        `physionet-data.mimiciv_hosp.omr`
    WHERE
        result_value IS NOT NULL
)

-- Pivot the latest results into columns for each subject_id
SELECT
    subject_id,
    MAX(CASE WHEN result_name = 'Weight (Lbs)' AND rn = 1 THEN result_value ELSE NULL END) AS weight_lbs,
    MAX(CASE WHEN result_name = 'Height (Inches)' AND rn = 1 THEN result_value ELSE NULL END) AS height_inches,
FROM
    ranked_results
GROUP BY
    subject_id
HAVING
    weight_lbs IS NOT NULL AND height_inches IS NOT NULL
ORDER BY
    subject_id;

CREATE OR REPLACE TABLE `mimic_ed.11_hf_final` AS
SELECT
    h.*,
    o.weight_lbs,
    o.height_inches
FROM
    `mimic_ed.10_hf_final` AS h
INNER JOIN
    `double-insight-425316-k4.mimic_ed.temp_omr_data` AS o
ON
    h.subject_id = o.subject_id;

-- Count outcomes of the final step
CREATE OR REPLACE TABLE `mimic_ed.count_11_hf_final` AS
SELECT
    ed_disposition,
    count(stay_id) AS count_stay_id
FROM
    `mimic_ed.11_hf_final`
GROUP BY
    ed_disposition;

-- Make query for CSV export
SELECT *
FROM `mimic_ed.11_hf_final`