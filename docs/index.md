# RECO: Recovery Companion

## Why Heart Failure?

1 in 33 Americans suffer from heart failure. Patients who are hospitalized frequently face worsened symptoms soon after discharge which, if not addressed swiftly, can lead to rehospitalization. Approximately 25% of heart failure patients are readmitted within 30 days of discharge, costing the healthcare system billions annually.

## Product Overview
RECO is designed to reduce readmission rates through continuous, AI-driven monitoring and support for heart failure patients. The platform gathers clinically relevant data, including symptoms, vital signs, and medication adherence, and compiles this information into structured reports for physicians.

<p align="center">
    <img src="images/MVP_Benefits.png" img width="75%"/>
</p>

## Technology and Architecture
### Technical Architecture
RECO’s architecture seamlessly integrates a user interface, chatbot, database, and summarization engine to provide an end-to-end solution for patient monitoring.

<p align="center">
    <img src="images/Overall_Architecture.png" img width="75%"/>
</p>

### Conversation Generation
RECO uses GPT-4 to simulate doctor-patient interactions. A system prompt guides the RECO chatbot to collect patient information as a doctor would in a routine appointment. A synthetic patient bot, modeled using anonymized real-world data from MIMIC-IV, interacts with the chatbot to generate dialogues that reflect actual heart failure patient-doctor interactions. Transcripts from these synthetic conversations are then a) evaluated to test the effectiveness of the chatbot, and b) processed by the summarization engine to produce summary reports.
<p align="center">
    <img src="images/Conversation_Generation_Diagram.png" img width="75%"/>
</p>

### Chatbot & Summarization Engine Evaluation
We developed evaluation criteria based on insights from domain experts, focusing on the chatbot’s ability to gather relevant patient data, exhibit empathy, and ensure summarization accuracy. These criteria were used for manual human evaluation of RECO-generated transcripts and summaries. We also created an LLM-as-a-judge system to automatically assess the transcripts and summaries against the established criteria. This system was iterated upon and validated against human evaluation results, ensuring it matched human judgment on most evaluation criteria. With a validated LLM-as-a-judge system in place, we were able to make scalable, iterative improvements to the RECO system.

<p align="center">
    <img src="images/Model_Evaluation.png" img width="75%"/>
</p>

## See RECO in Action
View our product demo by clicking the thumbnail below.

<p align="center">
    <a href="https://www.youtube.com/watch?v=9YP-0eKTouY">
    <img src="images/Reco_Demo_Thumbnail.png" img width="75%"/>
    </a>
</p>

## Key Project Impact
- **Improved Data Accuracy:** The summarization engine minimizes human error and provides consistent, relevant information for healthcare providers.
- **Enhanced Decision-Making:** Doctors receive concise summaries, facilitating quicker and better-informed clinical decisions.
- **Scalability:** The system allows for the management of larger patient volumes without overburdening healthcare providers.
- **Patient Engagement:** Studies show and patients agree: the chatbot is easier and more straightforward than traditional forms.

## Learn More

## Request a Live Demo
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

We would like to thank our course instructors (Professors Joyce Shen, Zona Kostic), the UC Berkeley I School, and all those who provided invaluable feedback and support throughout the project.

## Contributions

Contributions are welcome! Feel free to fork the project and submit a pull request. For major changes, please open an issue first to discuss your ideas.

Ensure that appropriate tests are updated when making changes.

<p align="center">
    <img src="images/reco_logo.png" img width="8%"/>
</p>

