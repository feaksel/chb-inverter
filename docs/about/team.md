# Team — Cereyan Hacıları

<figure markdown="span">
  ![Cereyan Hacıları on the demo stand](../assets/images/demo-stand-group-photo.jpeg){ loading=lazy width=80% }
  <figcaption>The four-person team: Furkan Emir Aksel, Ahmet Koçak, Faruk Gökhan Abay, Mücahit Aydın.</figcaption>
</figure>

The project group's name **Cereyan Hacıları** is Turkish for "The Current Pilgrims" — fitting for a power-electronics graduation project.

## Members and contributions

### Furkan Emir Aksel — Lead, firmware, dashboard

Project lead. Wrote the STM32 firmware end-to-end: the bare-metal CMSIS modulator (STAIR, PSC, STAIR_ALT), the supervisory FSM with the per-mode protection chain, the bit-banged MCP3201 driver with the runtime SPIINV mask, the UART command parser and 20 Hz telemetry frame, and the auto-start path with dashboard-aware cancellation. Built the **PySide6 operator dashboard** (architecture, scenario simulator, live serial path, replay support, the visual twin tab). Authored the firmware `CHANGELOG.md`, the `FIRST_BENCH_SESSION.md` and `HARDWARE_BRINGUP.md` bring-up documents. Drove the consolidation of the project into this monorepo.

GitHub: [@feaksel](https://github.com/feaksel).

### Ahmet Koçak — Hardware, bring-up

Hardware lead. Designed the KiCad schematic and PCB layout through all four iterations, owned the JLCPCB fab order workflow, and ran the bench bring-up sessions. Caught the iteration-3 grounding issue on the scope and drove the 4-layer stack-up redesign that fixed it in iteration 4. Owns the [BUILD GUIDE KICAD MISSMATCH](https://github.com/feaksel/chb-inverter/blob/main/docs/iteration-history/iteration-3.md) errata.

### Faruk Gökhan Abay — Simulation, analysis

Simulation lead. Built the Simulink models that produced the 4.9 % THD prediction and (more importantly) the **simulation evidence that killed the IR2110 + bootstrap path** before any silicon was committed. Authored sections of the ELE 402 interim report including the gate-driver and modulation comparison tables.

### Mücahit Aydın — Hardware, assembly

Hardware assembly + STM32 foundations. Did the populated-board assembly. Authored the early [STM32F303-RE notes](https://docs.google.com/document/d/1DIMxLaQtmeKM_b79f7GTw7JQwGADN5D7AVBmLAlodzk) and the [Foundations for the PWM generation](https://docs.google.com/document/d/1TzNnpJBHRkksMplpMHH699Cx1uxjyR5zOwXQ6L3Crec) document that gave the firmware its initial pin map (later corrected in iteration 3 to the as-built v4 layout).

## How the team divided the work

The project's natural decomposition into **hardware design + fab**, **firmware + dashboard**, **simulation + analysis**, and **assembly + bring-up** maps reasonably well onto the four members' roles, but in practice every milestone needed at least two people:

- Bench bring-up sessions: at least one operator at the supplies and one at the scope.
- PCB review before each fab order: schematic author + at least one independent reviewer.
- Firmware bring-up: firmware author + the hardware author who knew what was actually wired where.

The team's choice to commit to **PSC over IPD** (replacing the build-guide's modulation strategy mid-project) was made jointly after Ahmet's bench measurement of the bridge-1 thermal imbalance and Furkan's firmware-side analysis of what the IPD asymmetry meant for sustained operation. The simulation evidence from Faruk gave the team the confidence to make the change without losing weeks of bench time.

## Individual project logbooks (ELE 402, Spring 2025–2026)

Each team member maintained an individual project logbook tracking weekly progress through the Spring 2026 semester, per the ELE 402 course requirements. Each logbook reflects the member's individual perspective on the four hardware iterations, the firmware rewrite, and the bench validation.

| Member | Logbook |
|---|---|
| Furkan Emir Aksel | [PDF](../assets/pdfs/ELE402_Spring2026_Logbook_FurkanEmirAksel.pdf) (system + project engineering focus) |
| Ahmet Koçak | [PDF](../assets/pdfs/ELE402_Spring2026_Logbook_AhmetKocak.pdf) (hardware design + bring-up focus) |
| Faruk Gökhan Abay | [PDF](../assets/pdfs/ELE402_Spring2026_Logbook_FarukGokhanAbay.pdf) (simulation + analysis focus) |
| Mücahit Aydın | [PDF](../assets/pdfs/ELE402_Spring2026_Logbook_MucahitAydin.pdf) (hardware assembly + MCU foundations focus) |

Each logbook is regenerable from [`tools/generate-logbooks.py`](https://github.com/feaksel/chb-inverter/blob/main/tools/generate-logbooks.py).

## Where to reach the team

| Person | Best for |
|---|---|
| Furkan Emir Aksel | Firmware questions, dashboard, repository structure, this documentation site. Email: furkanemiraksel1@gmail.com |
| Ahmet Koçak | KiCad project, fab specifics, bench procedure, the iteration-3 → iteration-4 lessons |
| Faruk Gökhan Abay | Simulink models, THD analysis, gate-driver simulation methodology |
| Mücahit Aydın | Assembly procedure, early PWM design notes, STM32 pin map origin |
