-- Join detailed medication reconciliation data with the final HF dataset
CREATE OR REPLACE TABLE `mimic_ed.hf_filtered_with_meds` AS
SELECT
    t1.*,
    t2.ndc as med_ndc,
    t2.standardized_name as med_name,
    t2.gsn as med_gsn,
    t2.etccode as med_etccode,
    t2.etcdescription as med_etcdescription
FROM
    `double-insight-425316-k4.mimic_ed.temp_hf_standardized_medrecon` AS t2
INNER JOIN
    `double-insight-425316-k4.mimic_ed.11_hf_final` AS t1
ON
    t1.subject_id = t2.subject_id AND t1.stay_id = t2.stay_id;

-- Query to get CSV
SELECT *
FROM `mimic_ed.hf_filtered_with_meds`;

-- Do counts to check it mirrors sample sizes from python
SELECT
    ed_disposition,
    COUNT(DISTINCT(stay_id))
FROM
    `mimic_ed.hf_filtered_with_meds`
GROUP BY
    ed_disposition