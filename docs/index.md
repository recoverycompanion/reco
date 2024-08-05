# RECO: Recovery Companion

## Why Heart Failure?
Heart failure affects 1 in 33 Americans. Patients often experience worsening symptoms soon after hospital discharge, which can lead to rehospitalization. Nearly 25% of heart failure patients are readmitted within 30 days of discharge, costing the healthcare system billions annually. Resource constraints and the limitations of form-based methods of post-discharge monitoring often result in reactive rather than proactive care, leading to avoidable hospital readmissions.

## Product Overview
RECO: Recovery Companion is designed to reduce hospital readmissions by providing continuous, AI-driven monitoring and support for heart failure patients after discharge. The platform gathers clinically relevant data—such as symptoms, vital signs, and medication adherence—and compiles this information into structured reports for physicians. This proactive approach ensures better continuity of care and enables timely interventions.
<p align="center">
    <img src="images/MVP_Benefits.png" img width="75%"/>
</p>

## Architecture
RECO’s architecture seamlessly integrates a user interface, chatbot, database, and summarization engine to provide an end-to-end solution for patient monitoring.

<p align="center">
    <img src="images/Overall_Architecture_Cropped.png" img width="75%"/>
</p>

### Chatbot
The RECO chatbot is designed to simulate a doctor’s role in collecting patient information. Using a system prompt, the chatbot uses GPT-4o to guide conversations, asking questions and gathering data just as a doctor would during a routine appointment.

### Summarizer
The RECO summarization engine analyzes the conversation transcript using a system prompt with GPT-4o-mini, extracting key details like symptoms, vitals, and medications. It then distills this information into structured summaries that are formatted and emailed as PDF reports to physicians.

## Modeling Approach
Development of the RECO system involved simulating conversations with synthetic patients, and establishing an automated evaluation system to enable iterative improvements.
<p align="center">
    <img src="docs/images/Modelling_Approach_2.jpeg" img width="75%"/>
</p>

### Conversation Simulation
We simulated chatbot-patient conversations by having the RECO chatbot interact with synthetic patient bots. Synthetic patient bots are modeled using anonymized real-world patient data from MIMIC-IV and can take on various personas, including a cooperative patient who readily provides information and a reluctant patient who withholds details. These simulated conversations generate transcripts that are used both for evaluation and as input for the summarizer.

### Evaluation
We developed an *LLM-as-a-judge* system to automatically assess the transcripts and summaries against evaluation criteria that focused on the system’s ability to gather relevant patient data (symptoms, vitals, and medications), maintain dialogue quality (empathy, refraining from diagnosis), and ensure summarization accuracy. To ensure the reliability of *LLM-as-a-judge*, we compared its outputs (binary classifications) to the ground truth of human judgment and iteratively refined the system to enhance its accuracy.

<p align="center">
    <img src="images/Model_Evaluation.png" img width="75%"/>
</p>

#### Iterative Improvement
Using the automated evaluation pipeline, we tested and modified RECO's underlying models (e.g., GPT-3.5-turbo vs. GPT-4o-mini vs. GPT-4o) and adjusted prompts to improve conversation quality, such as nudging reluctant patients to provide more information.

## See RECO in Action
View our product demo by clicking the thumbnail below.

<p align="center">
    <a href="https://www.youtube.com/watch?v=9YP-0eKTouY">
    <img src="images/Reco_Demo_Thumbnail.png" img width="75%"/>
    </a>
</p>

If you would like a live demo, please reach out to <reco.recovery.companion@gmail.com>.

## Project Impact
RECO addresses key challenges in post-discharge heart failure management by providing:
- **Enhanced Decision-Making:** Doctors receive concise summaries, facilitating quicker and better-informed clinical decisions.
- **Scalability:** The system allows for the management of larger patient volumes without overburdening healthcare providers.
- **Patient Engagement:** Studies and patient feedback indicate that the chatbot is easier and more straightforward than traditional forms.

## Learn More
View the detailed presentation on [SlideShare](https://www.slideshare.net/secret/FWIu2e4jjTyvmL).

## Team
RECO is a capstone project developed by a team of us at the University of California, Berkeley as part of our Master of Information and Data Science program.

<table>
  <tr>
    <td><img src="images/Team_Member_Photos/Mike_Khor.png" width="200"></td>
    <td><img src="images/Team_Member_Photos/Gary_Kong.png" width="200"></td>
    <td><img src="images/Team_Member_Photos/Annie_Friar.png" width="200"></td>
    <td><img src="images/Team_Member_Photos/Farid_Gholitabar.png" width="200"></td>
  </tr>
  <tr>
    <td style="text-align: center;"><a href="mailto:mike.khor@berkeley.edu">Mike Khor</a></td>
    <td style="text-align: center;"><a href="mailto:garykong@berkeley.edu">Gary Kong</a></td>
    <td style="text-align: center;"><a href="mailto:anniefriar@berkeley.edu">Annie Friar</a></td>
    <td style="text-align: center;"><a href="mailto:farid.gholitabar@berkeley.edu">Dr. Farid Gholitabar</a></td>
  </tr>
</table>

## Acknowledgements
We would like to thank our course instructors (Professors Joyce Shen, Zona Kostic), the UC Berkeley I School, and all those who provided invaluable feedback and support throughout the project.

## Contributions
Contributions are welcome! Feel free to fork the project and submit a pull request. For major changes, please open an issue first to discuss your ideas.

Ensure that appropriate tests are updated when making changes.

<p align="center">
    <img src="images/reco_logo.png" img width="8%"/>
</p>

