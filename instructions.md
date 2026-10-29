**This is a converted version of the original file 'instructions.pdf'.**

# **Task 1: UHF Antenna Deployment Test Plan**

You are a System Test Engineer at EnduroSat. Your team is responsible for verifying the deployment
algorithm of the 2U UHF Antenna before it is integrated into the satellite.


Based on the provided documentation, your task is to create a test plan to verify the functionality of
the antenna deployment mechanism. You do not need to test every possibility. Instead, identify and outline
the three (3) most critical test cases you would execute to gain confidence in the system.


For each of the three test cases, you must specify the following:


   - **Test Case Title:** A short, descriptive name (e.g., "Nominal Deployment via MCU Command").


   - **Objective:** A single sentence explaining why this test is important.


   - **High-Level Execution Steps:** A brief, numbered list of actions to perform the test.


   - **Expected Outcome / Success Criteria:** How you would determine if the test passed.


**Deliverable:**


Please write your answer in a plain text file. Focus on demonstrating your understanding of the
system's logic, including its timing and redundancy. Clarity and prioritization are more important than detail.


**Description of the deployment mechanism**


**UHF 2U Antenna deployment system**


The UHF 2U antenna has 4 rods, 4 burn resistors, and 2 burn wires (denoted in red in the figure
below). The 4 burn resistors are named A1 and A2 (denoted in green in the figure below), and B1 and B2
(denoted in blue in the figure below). Resistors A1 and B1 are placed next to each other and are tied with
one burn wire, which, when cut, releases rods 1 and 2. Resistors A2 and B2 are placed next to each other
and are tied with a second burn wire, which, when cut, releases rods 3 and 4.

![](C:/Users/ans1sf/Desktop/Git_Repos/FuSa_AI_Repo/fusa_ai/agents/FuSa_AI_Agent/knowledge/vdb_files/images/instructions.pdf-0-0.png)


_Figure 1: Figure 1: 2U antenna_
_schematics showing the 4 rods, 4 burn_
_resistors and 2 burn wires_


**MCU and GPO Deployment algorithms**


The UML diagram below refers to MCU Deployment Algorithm and GPO Deployment Algorithm. These two
algorithms are identical in terms of what burn resistors are activated when and for how long with the only
difference being that the MCU Deployment Algorithm is activated by the Antenna MCU, while the GPO
Deployment Algorithm is activated by the UHF Transceiver GPOs (Release A and Release B).


The MCU Deployment Algorithm and GPO Deployment Algorithm follow the same sequence shown in the
figure below. First resistors A1 and A2 are turned on. 5 seconds later resistors B1 and B2 are turned on. 5

seconds after that resistors A1 and A2 are turned off. 5 seconds after that resistors B1 and B2 are turned off.

This logic means that each pair (A1 and A2, as well as B1 and B2) are turned on for 10 seconds each but
they are staggered by a 5 second delay. This ensures that if there is an issue with either pair A or pair B, the
other pair will be on for 10 seconds. If both pairs are working, then all resistors will be on for 5 seconds.

![](C:/Users/ans1sf/Desktop/Git_Repos/FuSa_AI_Repo/fusa_ai/agents/FuSa_AI_Agent/knowledge/vdb_files/images/instructions.pdf-1-0.png)


_Figure 2: Figure 2: Deployment algorithm (both MCU_
_and GPO)_


For the sake of redundancy both the Antenna MCU and the UHF transceiver can release the antenna rods.
The logic is described in the UML diagram below - 2U_UHF_deployment.svg


