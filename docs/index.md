# RECO: Recovery Companion

We developed a conversational AI that assists patients with heart failure (HF) who have recently been discharged from the hospital. HF is a condition where the heart struggles to pump blood efficiently, often due to damage or disease affecting the heart's muscle. Patients frequently face worsened symptoms soon after hospital discharge, which if not addressed swiftly, can lead to rehospitalization.

RECO aims to monitor these patients by routinely asking about their symptoms, vital signs, and medication adherence. It will then compile this information into a structured report for their physician. This proactive approach helps in detecting any worsening of the condition early, potentially prompting timely medical interventions. The conversational AI is not designed to diagnose conditions or offer medical advice directly to patients but serves as a crucial communication bridge between patients and their healthcare providers.

## Reco Demo

<p align="center">
    <a href="https://www.youtube.com/watch?v=9YP-0eKTouY">
    <img src="images/Reco_Demo_Thumbnail.png" img width="75%"/>
    </a>
</p>

## Features

- **Symptom Tracking:** Monitors patient-reported symptoms and vitals through clinically informed daily interactions.
- **Summarized Report:** Accurate summary of patient encounter is automatically sent to the patient's provider for review.

## Technical Architecture

<p align="center">
    <img src="images/Overall_Architecture.png" img width="75%"/>
</p>

RECO is built using the following technologies:

- **Frontend:** Streamlit for interactive web interface.
- **Backend:** Python, Flask for API management, and handling server-side logic.
- **AI Model:** Utilizes OpenAI's GPT models for natural language understanding and generation.
- **Database:** PostgreSQL for storing patient data securely.

## Request for a Live Demo

If you would like a live demo, please reach out to <reco.recovery.companion@gmail.com>.

## Team

RECO is a capstone project developed by a team of us at the University of California, Berkeley as part of our Master of Information and Data Science program.

<table>
  <tr>
    <td><img src="images/Team_Member_Photos/Mike_Khor.png" width=200></td>
    <td><img src="images/Team_Member_Photos/Gary_Kong.png" width=200></td>
    <td><img src="images/Team_Member_Photos/Annie_Friar.png" img width=200></td>
    <td><img src="images/Team_Member_Photos/Farid_Gholitabar.png" width=200></td>
  </tr>
  <tr>
    <td><center><a href="mailto:mike.khor@berkeley.edu">Mike Khor</a></center></td>
    <td><center><a href="mailto:garykong@berkeley.edu">Gary Kong</a></center></td>
    <td><center><a href="mailto:anniefriar@berkeley.edu">Annie Friar</a></center></td>
    <td><center><a href="mailto:farid.gholitabar@berkeley.edu">Dr. Farid Gholitabar</a></center></td>
  </tr>
 </table>

## Acknowledgements

We would like to thank our course instructors (Professors Joyce Schen, Zona Kostic), the UC Berkeley I School, and all those who provided invaluable feedback and support throughout the project.

## Contributions

Contributions are welcome! Feel free to fork the project and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
