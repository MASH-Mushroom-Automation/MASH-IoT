# Comprehensive Optimization of Artificial Intelligence Actuator Control for White Oyster Mushroom Cultivation via the M.A.S.H. System

## Introduction

The intersection of mycological science and automated environmental control represents a paradigm shift for agricultural stability in tropical climates, particularly within the Philippines. The white oyster mushroom, Pleurotus florida, serves as an ideal biological model for this technological integration due to its rapid colonization rates and high sensitivity to microclimatic fluctuations.1 The development of the Mushroom Automation with Smart Hydro-environment (M.A.S.H.) system addresses the inherent challenges faced by small-scale farmers, including inconsistent yields, contamination risks, and the physical burden of manual monitoring.1 Central to this system's efficacy is the optimization of its scikit-learn AI model, which must translate complex sensor data into precise actuator commands while adhering to strict biological requirements and safety constraints.

## Technical Framework and Biological Requirements for Pleurotus florida

The cultivation of Pleurotus florida is characterized by a high biological efficiency, often reaching 100% when grown on optimized lignocellulosic substrates.2 However, achieving this potential requires the system to maintain environment-specific setpoints across distinct growth phases. In the tropical context of the Philippines, where ambient temperatures often exceed 30.0 C and humidity levels fluctuate significantly, the role of automated climate control becomes critical for preventing metabolic stress and crop failure.5

### Environmental Setpoints for Spawn Run and Colonization

The initial vegetative phase, known as the spawn run, involves the colonization of the substrate by fungal mycelia. This stage thrives under conditions that would be detrimental to the later fruiting bodies. Research indicates that Pleurotus florida mycelium exhibits optimal radial growth at temperatures between 25.0 C and 30.0 C.5 Maintaining this elevated temperature range is essential for rapid colonization, which helps the fungus outcompete opportunistic contaminants like Trichoderma spp..5

Carbon dioxide ($CO_{2}$) plays a unique role during colonization. Unlike green plants, Pleurotus species are highly tolerant of, and stimulated by, high concentrations of $CO_{2}$ during the spawn run.3 Concentrations between 10,000 ppm and 20,000 ppm are considered ideal for promoting vigorous mycelial expansion.3 The M.A.S.H. system must recognize this phase to suppress the exhaust fan, thereby allowing metabolic $CO_{2}$ to accumulate and benefit the growth rate. Humidity during this phase should remain moderate, typically between 70% and 80%, to prevent substrate desiccation without inducing condensation that could lead to anaerobic zones within the fruiting bags.13

### Critical Parameters for the Fruiting Phase

The transition to the reproductive or fruiting phase requires a strategic "environmental shock." This transition is triggered by three primary variables: a reduction in temperature, a drastic decrease in $CO_{2}$ through fresh air exchange (FAE), and an increase in relative humidity.9 For Pleurotus florida, pinning is most effectively induced when the temperature is lowered to 20.0 C–24.0 C and humidity is spiked to nearly 100%.5

Based on the M.A.S.H. system's dashboard (Image 2), the specific targets for the fruiting room are set at 24.0 C for temperature, 90.0% for humidity, and less than 1,000 ppm for $CO_{2}$.1 These targets align with academic literature suggesting that consistent levels of 85%–95% RH and temperatures below 26.0 C are necessary for high-quality fruit body development.5 Deviations from these targets result in immediate morphological defects. For example, high temperatures (>30.0 C) cause metabolic stress, leading to shriveled caps and stalled growth, while excessive $CO_{2}$ (>1,000 ppm) induces "leggy" growth characterized by elongated stems and underdeveloped, pin-like caps.10

| Environmental Factor | Target Range (Fruiting) | Current Condition (Image 4) | Deviation      |
| -------------------- | ----------------------- | --------------------------- | -------------- |
| Temperature          | 24.0 C                  | 28.2 C                      | $+4.2$ C       |
| Relative Humidity    | 90.0%                   | 80.9%                       | $-9.1$%        |
| Carbon Dioxide       | < 1000 ppm              | N/A (Image 4)               | Check Required |

## Analysis of Current Environmental Deviations and Psychrometric Impact

The latest dashboard snapshot (Image 4) presents a critical scenario where the temperature is 28.2 C and humidity is 80.9%. This state represents a significant departure from the target 24.0 C and 90.0% RH. The $4.2$ C temperature excess is particularly concerning in the Philippine lowland context, where such heat can rapidly desiccate the mushroom primordia.5

### The Evaporative Cooling Mechanism

The primary tool for correcting this deviation is the ultrasonic Mist Maker. Beyond providing humidity, the misting system acts as an evaporative cooler. As ultra-fine water droplets (3–5 microns) are introduced into the air by the 10-head mist maker, they absorb latent heat from the surrounding environment to undergo phase change.23 Research into ultrasonic mist generators indicates they can achieve a temperature drop ($T_{drop}$) of approximately 4.3 C to as much as 12.0 C depending on the initial dry-bulb temperature and humidity.25

In the current state of 28.2 C and 80.9% RH, the air still has a capacity to absorb moisture before reaching saturation (dew point). By activating the Mist Maker and the Humidifier Fan, the M.A.S.H. system can utilize this adiabatic cooling effect to drive the temperature down toward the 24.0 C target while simultaneously raising the RH toward 90.0%.23 This dual-action correction is far more energy-efficient than mechanical refrigeration and is perfectly suited for the resource-constrained smallholder farms the M.A.S.H. system serves.1

### Impact of Stagnant Carbon Dioxide

While Image 4 does not explicitly show $CO_{2}$ levels for the 28.2 C/80.9% state, Image 2 (a similar condition) shows 934 ppm, and Image 1 shows Spawning Room levels at 1105 ppm.1 Mushrooms are constant respiratory organisms, consuming $O_{2}$ and releasing $CO_{2}$ throughout their development.21 In a sealed growing chamber, $CO_{2}$ can quickly exceed the 1,000 ppm threshold, especially as the fungal biomass increases.30 Excessive $CO_{2}$ inhibits the formation of the pileus (cap) and favors the growth of the stipe (stem), which reduces the marketability and nutritional density of the harvest.10 Consequently, the integration of the "Air Flow" system—comprised of the Exhaust Fan and Intake Blower—is vital for maintaining the gas exchange required for reproductive success.1

## Optimization of the scikit-learn AI Model for Actuator Control

The M.A.S.H. system employs a sophisticated machine learning pipeline to manage the grow chamber. As indicated in the system insights (Image 1), the architecture utilizes an Isolation Forest for anomaly detection and a Decision Tree for the actuation model.1 This choice of algorithms is highly appropriate for the complex, non-linear dynamics of a mushroom fruiting chamber.

### Isolation Forest for Data Hygiene

In high-humidity environments (85%–95% RH), electronic sensors are prone to temporary failure, drift, or noise.12 Condensation on the sensor surface can lead to "flatline" readings or extreme spikes that do not reflect actual air conditions. The Isolation Forest algorithm excels at identifying these outliers by isolating observations through random partitioning.1 By filtering the raw telemetry through this model, the M.A.S.H. system ensures that the actuator control logic is based on verified, clean data, preventing unnecessary or harmful fan and mist maker cycles.

### Decision Tree Logic for Multi-Output Actuation

The sklearn.tree.DecisionTreeClassifier serves as the brain of the automated control system. It maps the filtered environmental inputs ($T, H, C$) to a four-element binary output vector representing the states of the Mist Maker, Humidifier Fan, Exhaust Fan, and Intake Blower.1 The model is trained to reach a specific state that maximizes the "purity" of the environmental conditions relative to the targets.34

A primary advantage of the Decision Tree is its interpretability as a "white box" model. For professional mycologists and system administrators, the logic can be visualized and validated using entropy and information gain calculations.33 The entropy ($E$) of the system state is defined by the probability of being in an optimal vs. sub-optimal growth condition:

$$E = -\sum_{i=1}^{n} p_i \log_2(p_i)$$

The scikit-learn model iteratively splits the sensor data to minimize this entropy, effectively "learning" that when the temperature is 28.2 C and humidity is 80.9%, the optimal path is the immediate activation of the humidification system.34

### Multi-Output Classifier Implementation

Since the system must control four actuators simultaneously, the sklearn.multioutput.MultiOutputClassifier is employed. This meta-estimator fits one classifier per target variable, allowing the model to handle dependencies between actuators—such as the requirement that the Humidifier Fan should always be active when the Mist Maker is ON to ensure mist distribution.16

## Actuator Prioritization and Operational Logic

To address the current critical deviations (28.2 C / 80.9% RH) while adhering to safety and efficiency constraints, a prioritized actuation plan must be hard-coded into the AI model's training parameters. This plan acknowledges the user-defined safety constraint: the Exhaust Fan must never run while the Humidifier System is active.1

### Priority 1: Humidification and Evaporative Cooling

The highest priority in the current "Critical" condition is the stabilization of temperature and humidity. Because the humidity (80.9%) is below the minimum threshold (85%) and the temperature (28.2 C) is above the target (24.0 C), the system must engage the Mist Maker and Humidifier Fan immediately.1

- Mist Maker (ON): The 10-head mist maker must run at maximum atomization output ($7 kg/h$) to provide both moisture and cooling.1
- Humidifier Fan (ON): This fan must operate concurrently to push the generated mist through the air duct system, ensuring even distribution across all tiers of the fruiting bags.1
- Exhaust Fan (OFF): Mandatory safety interlock. Activating the exhaust would create negative pressure that pulls the newly created mist out of the chamber before it can settle or evaporate, wasting water and potentially causing moisture buildup in the exhaust ducting.1
- Intake Blower (OFF or PULSED): To maintain positive pressure and assist the mist flow without diluting the humidity too rapidly, the intake blower should be off or run at a minimal duty cycle.

### Priority 2: Gas Exchange and Stale Air Removal (Air Flow System)

Once the humidity target (90%) is approached or the temperature has successfully dropped to a safe range (25 C), the system transitions to gas exchange. This shift is essential to prevent $CO_{2}$ levels from exceeding 1,000 ppm.10

- Mist Maker (OFF): To allow the exhaust cycle to begin.
- Humidifier Fan (OFF): Prevents blowing dry air or forcing moisture into the intake during the exhaust phase.
- Exhaust Fan (ON): Placed high in the chamber (or low to target heavy $CO_{2}$ depending on ducting design), it removes stale, $CO_{2}$-rich air.21
- Intake Blower (ON): Works in tandem with the exhaust to provide Active Fresh Air Exchange (FAE). Fresh, oxygenated air is drawn in to replace the exhausted volume.21

### Decision Logic Matrix for scikit-learn Training

The following table outlines the logic states that the AI model should be trained to implement based on the Fruiting Room targets:

| Scenario             | Temp State   | Humidity State | Mist Maker | Humidifier Fan | Intake Blower | Exhaust Fan |
| -------------------- | ------------ | -------------- | ---------- | -------------- | ------------- | ----------- |
| Current Deviation    | High (>26 C) | Low (<85%)     | ON         | ON             | OFF           | OFF         |
| Pinning Trigger      | Normal       | High (>95%)    | ON         | ON             | OFF           | OFF         |
| Stale Air ($CO_{2}$) | Normal       | Normal         | OFF        | OFF            | ON            | ON          |
| Cooling (High RH)    | High (>26 C) | High (>92%)    | OFF        | OFF            | ON            | ON          |
| Equilibrium          | 24.0 C       | 90.0%          | OFF        | OFF            | PULSE         | OFF         |

## System Architecture and Operational Continuity

The M.A.S.H. system's hardware and software architecture are designed to support this complex logic even under suboptimal conditions such as network instability or power fluctuations, which are common in the Philippines.1

### Multi-Tier Distributed Architecture

The system operates across four distinct layers to ensure modularity and scalability 1:

- Tier 1 (Frontend Layer): Developed with Flutter and Next.js, providing growers with real-time dashboards and sellers with e-commerce management tools.
- Tier 2 (Backend Layer): A NestJS API server that manages business logic, WebSocket connections for real-time alerts, and the MQTT broker (HiveMQ Cloud) for IoT communication.
- Tier 3 (Data & Services Layer): Utilizing a polyglot database strategy. PostgreSQL (via Neon/Prisma) handles persistent user and transaction data, while Firebase Firestore manages real-time NoSQL profile syncing.
- Tier 4 (IoT Edge Layer): The physical core, consisting of a Raspberry Pi 3B gateway and Arduino Uno firmware. The Raspberry Pi runs a Flask server for local control logic, ensuring that if the internet connection is lost, the Decision Tree model can still function at the edge.1

### Data Persistence and Offline-First Logic

A critical feature of the M.A.S.H. system is the use of SQLite for local data buffering on the Raspberry Pi.1 During internet outages, the system continues to poll sensors and execute the scikit-learn actuation model, logging all events to the local SQLite database. Once connectivity is restored, the local data is synchronized with the cloud PostgreSQL database. This ensures that the history of the mushroom's environmental exposure is never lost, which is vital for quality grading on the MashMarket platform.1

## Economic and Social Impact of Automated Mushroom Cultivation

The Philippine mushroom market demonstrates a compound annual growth rate (CAGR) of 5.76%, with the market size projected to reach USD 2,377.43 million by 2033. Despite this potential, local growers currently satisfy only 10% of demand, largely due to the production inefficiencies the M.A.S.H. system aims to solve.

### Profitability and Efficiency Gains

Research indicates that small-scale mushroom enterprises in regions like Nueva Ecija and Bukidnon can achieve high returns on investment (ROI), ranging from 140% to 191%. However, these returns are often threatened by high contamination rates (up to 30%) and labor-intensive manual watering.1 By automating environmental regulation, the M.A.S.H. system has the potential to reduce contamination by up to 60% and improve yields by 30%–49% compared to traditional methods.1

Furthermore, the integration of an e-commerce platform (MashMarket) allows farmers to bypass middle-men, increasing their profit margins.1 The AI-driven quality grading—informed by the grow chamber's historical data—provides consumers with transparency and assurance of freshness, supporting the 83% of Filipino shoppers who are willing to pay more for AI-enhanced experiences.

### Contribution to Sustainability and Food Security

Mushroom cultivation promotes the circular bioeconomy by converting agricultural waste (rice straw, banana leaves) into high-protein food.2 The M.A.S.H. system enhances this process by optimizing resource use. The use of smart sensors and automation can reduce water and nutrient waste by 30% and energy consumption by 18% [Malakar et al., 2025]. This alignment with Sustainable Development Goals (SDGs) regarding poverty alleviation, waste recycling, and food security underscores the broader significance of the project.1

## Final Synthesis and Recommendations for AI Optimization

To satisfy the original request and maximize the performance of the Pleurotus florida cultivation cycle, the M.A.S.H. AI model must be fine-tuned to handle the current deviations (28.2 C / 80.9% RH) with a long-term perspective on seasonal resilience.

### Strategic Actuator Deployment Summary

In the current critical state, the AI model should immediately trigger the Priority 1 Humidification System. The logic flow is as follows:

- Verify Data: The Isolation Forest must confirm the 28.2 C and 80.9% RH readings are not sensor artifacts caused by localized condensation.1
- Activate Humidification: The Mist Maker and Humidifier Fan are engaged. The target is to reach 90% RH.
- Enforce Safety Gate: The Exhaust Fan is locked in the OFF position while the Mist Maker is active.1
- Monitor Temperature Drop: As the humidity increases, the system monitors for adiabatic cooling. If the temperature remains above 26.0 C even after reaching 90% RH, the system must transition to Priority 2.
- Exhaust Cycle: Once the Mist Maker is deactivated, the Exhaust Fan and Intake Blower are activated to flush out the heat and $CO_{2}$, utilizing the 'Air Flow' system to stabilize the chamber.1

### Model Training Refinement

The scikit-learn model should be retrained with "season-aware" parameters. In the Philippine context, summer months (March–May) present the highest risk of low humidity and high temperature.7 The Decision Tree should be weighted to respond more aggressively to temperature spikes during these months. Additionally, the integration of HEPA-filtered intake blowers must be maintained as a constant to prevent the introduction of airborne spores and competitors during the high-airflow exhaust cycles.1

By adhering to these environmental targets and logic priorities, the M.A.S.H. system provides a robust, reliable, and scientifically grounded solution for automating white oyster mushroom cultivation. This technology empowers smallholder farmers to achieve consistent, high-yield harvests, bridging the gap between traditional agricultural knowledge and modern computational intelligence.

## Works Cited

- MASH Final.pdf
- Cultivation and Nutritional Value of Prominent Pleurotus spp.: An Overview - PMC - NIH, accessed March 29, 2026, https://pmc.ncbi.nlm.nih.gov/articles/PMC7832515/
- Influence of CO2 Concentration on the Mycelium Growth of Three Pleurotus Species - MPG.PuRe, accessed March 29, 2026, https://pure.mpg.de/rest/items/item_39635/component/file_52583/content
- Effects of Various Ventilation Systems on the Carbon Dioxide Concentration and Fruiting Body Formation of King Oyster Mushroom (Pleurotus eryngii) Grown in Culture Bottles | Request PDF - ResearchGate, accessed March 29, 2026, https://www.researchgate.net/publication/273991621_Effects_of_Various_Ventilation_Systems_on_the_Carbon_Dioxide_Concentration_and_Fruiting_Body_Formation_of_King_Oyster_Mushroom_Pleurotus_eryngii_Grown_in_Culture_Bottles
- Influence on Temperature and Relative Humidity on Fruiting Body Production of Pleurotus Florida (Oyster Mushrooms) in the Cropping Room - ijrrr, accessed March 29, 2026, https://www.ijrrr.com/papers11-1/paper16-Influence%20on%20Temperature%20and%20Relative%20Humidity%20on%20Fruiting%20Body%20Production%20of%20Pleurotus%20Florida%20_Oyster%20Mushrooms_%20in%20the%20Cropping%20Room.pdf
- Application of Temperature and Humidity Control Technology in The Oyster Mushroom Cultivation Business - Semantic Scholar, accessed March 29, 2026, https://pdfs.semanticscholar.org/5881/2bfb00c2c2b7f2a53127b30c1a911581cede.pdf
- CULTIVATION OF OYSTER MUSHROOM (PLEUROTUS FLORIDA) IN VARIOUS SEASONS ON PADDY STRAW, accessed March 29, 2026, http://www.rjlbpcs.com/article-pdf-downloads/2019/31/708.pdf
- The Effects of Temperature and Nutritional Conditions on Mycelium Growth of Two Oyster Mushrooms (Pleurotus ostreatus and Pleurotus cystidiosus) - PMC, accessed March 29, 2026, https://pmc.ncbi.nlm.nih.gov/articles/PMC4397375/
- SL448/SS662: D.I.Y. FunGuide: Grow Your Own Oyster Mushrooms at Home, accessed March 29, 2026, https://ask.ifas.ufl.edu/publication/SS662
- 7 Factors Affecting Mushroom Cultivation - Atlas Scientific, accessed March 29, 2026, https://atlas-scientific.com/blog/factors-affecting-mushroom-cultivation/
- Influence of CO2 concentration on the mycelium growth of three pleurotus species - SciSpace, accessed March 29, 2026, https://scispace.com/pdf/influence-of-co2-concentration-on-the-mycelium-growth-of-3za7oqmsg1.pdf
- Mushroom Cultivation Temperature and Climate Control: Choosing the Right Sensors is Crucial - E+E Elektronik, accessed March 29, 2026, https://www.epluse.com/news/blog/detail/2025-08-27-mushroom-cultivation-temperature/
- The 4 culture parameters to master for growing mushrooms - La Mycosphère, accessed March 29, 2026, https://lamycosphere.com/en-de/blogs/the-future-is-fungi/the-4-culture-parameters-to-master
- How Much Humidity for Mushroom Grow Tent: Complete Guide 2025, accessed March 29, 2026, https://www.gorillagrowtent.com/blogs/news/how-much-humidity-for-mushroom-grow-tent
- Humidity Control Techniques For Indoor Mushroom Cultivation - Yake Climate Dehumidifer Manufacturer, accessed March 29, 2026, https://yakeclimate.com/humidity-control-techniques-for-indoor-mushroom-cultivation/
- Mastering Humidity: Perfectly Balancing Humidity for Optimal Mushroom Cultivation. | SPeS, accessed March 29, 2026, https://www.spes.co.za/how-the-humidity-level-is-controlled-and-maintained-in-a-grow-room-for-mushroom-cultiativation/
- Controlling Humidity and Why It's Important For Mushroom Cultivation, accessed March 29, 2026, https://www.redwoodmushroomsupply.com/blogs/mushroom-cultivation/controlling-humidity-and-why-it-s-important-for-mushroom-cultivation
- Factors affecting mushroom Pleurotus spp - PMC - NIH, accessed March 29, 2026, https://pmc.ncbi.nlm.nih.gov/articles/PMC6486501/
- (PDF) CULTIVATION OF Pleurotus florida BY STANDARD PROTOCOL - ResearchGate, accessed March 29, 2026, https://www.researchgate.net/publication/385204759_CULTIVATION_OF_Pleurotus_florida_BY_STANDARD_PROTOCOL
- Precision climate control for optimal growth in mushroom farming - Fancom BV, accessed March 29, 2026, https://www.fancom.com/blog/precision-climate-control-for-optimal-growth-in-mushroom-farming
- Fresh Air Exchange For Mushroom Cultivation, accessed March 29, 2026, https://www.redwoodmushroomsupply.com/blogs/mushroom-cultivation/fresh-air-exchange-for-mushroom-cultivation
- How To Control Temperature For Mushroom Growing - Atlas Scientific, accessed March 29, 2026, https://atlas-scientific.com/blog/how-to-control-temperature-for-mushroom-growing/
- How Does An Evaporative Cooling System Work in Mushroom Houses? - News, accessed March 29, 2026, https://www.vrcoolertech.com/news/how-does-an-evaporative-cooling-system-work-in-77276231.html
- Grow Mushrooms Like a Pro: The Secret Benefits of Ultrasonic Fog and Custom DIY Humidifiers - The House of Hydro, accessed March 29, 2026, https://thehouseofhydro.com/blogs/fog-blog/grow-mushrooms-like-a-pro-the-secret-benefits-of-ultrasonic-fog-and-custom-diy-humidifiers
- Experimental study of an ultrasonic mist generator as an evaporative cooler - ResearchGate, accessed March 29, 2026, https://www.researchgate.net/publication/346392268_Experimental_study_of_an_ultrasonic_mist_generator_as_an_evaporative_cooler
- Cool humidification - using humidifiers for evaporating cooling - Condair Group, accessed March 29, 2026, https://www.condairgroup.com/Energy-optimization/cool-humidification-evaporative-cooling-humidifier
- Cool humidification - using humidifiers for evaporating cooling - Condair, accessed March 29, 2026, https://www.condair.com.au/knowledge-hub/cool-humidification
- Mushroom cultivation and humidity control - Ikeuchi Europe, accessed March 29, 2026, https://www.ikeuchi.eu/humidity-control-for-mushroom-cultivation/
- Why Mushroom Growth Requires a Fan & Fresh Air Exchange | Felix Smart, accessed March 29, 2026, https://www.felixsmart.com/blogs/mushroom-automation/why-a-fan-for-fresh-air-exchange-is-important-for-indoor-mushroom-growth
- Why You Need A CO2 Meter For Growing Mushrooms - Atlas Scientific, accessed March 29, 2026, https://atlas-scientific.com/blog/why-you-need-a-co2-meter-for-growing-mushrooms/
- Do You Really Need a Fan for Mushroom Growth?, accessed March 29, 2026, https://zombiemyco.com/blogs/mushrooms/mushroom-growth-do-you-really-need-a-fan-1
- Air Conditioning Systems for Mushroom Cultivation: Choosing the Right Sensors Is Crucial, accessed March 29, 2026, https://sensorsandtransmitters.com/air-conditioning-systems-for-mushroom-cultivation-choosing-the-right-sensors-is-crucial/
- 1.10. Decision Trees — scikit-learn 1.8.0 documentation, accessed March 29, 2026, https://scikit-learn.org/stable/modules/tree.html
- DecisionTreeClassifier — scikit-learn 1.8.0 documentation, accessed March 29, 2026, https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html
- Decision Tree Helpers for Mushroom Classification | by Q - Medium, accessed March 29, 2026, https://medium.com/@q765524692/decision-tree-helpers-for-mushroom-classification-df3ec9c940ed
- Implementing a Decision Tree from Scratch for Mushroom Classification | by Kush Patel, accessed March 29, 2026, https://medium.com/@patelkush2582000/implementing-a-decision-tree-from-scratch-for-mushroom-classification-d43c1da49783
- machine-learning-articles/building-a-decision-tree-for-classification-with-python-and-scikit-learn.md at main - GitHub, accessed March 29, 2026, https://github.com/christianversloot/machine-learning-articles/blob/main/building-a-decision-tree-for-classification-with-python-and-scikit-learn.md?plain=1
- MultiOutputClassifier — scikit-learn 1.8.0 documentation, accessed March 29, 2026, https://scikit-learn.org/stable/modules/generated/sklearn.multioutput.MultiOutputClassifier.html
- 1.12. Multiclass and multioutput algorithms - Scikit-learn, accessed March 29, 2026, https://scikit-learn.org/stable/modules/multiclass.html
- Fruiting chamber advice!? : r/mycology - Reddit, accessed March 29, 2026, https://www.reddit.com/r/mycology/comments/1ppm3k6/fruiting_chamber_advice/
- Better Airflow, Better Mushrooms: Solving Grow Room Problem - YouTube, accessed March 29, 2026, https://www.youtube.com/watch?v=62ByTSkCudU
- jupyter_nbs_empirical/data_filtering_[process]valid_ast.ipynb at master - GitHub, accessed March 29, 2026, https://github.com/PELAB-LiU/jupyter_nbs_empirical/blob/master/data_filtering_%5Bprocess%5Dvalid_ast.ipynb
- A Review of Nature-Based Solutions for Valorizing Aromatic Plants' Lignocellulosic Waste Through Oyster Mushroom Cultivation - MDPI, accessed March 29, 2026, https://www.mdpi.com/2071-1050/17/10/4410
- (PDF) Growth and yield performance of Pleurotus on selected Lignocellulosic wastes in the vicinity of PUP main campus, Philippines - ResearchGate, accessed March 29, 2026, https://www.researchgate.net/publication/349220914_Growth_and_yield_performance_of_Pleurotus_on_selected_Lignocellulosic_wastes_in_the_vicinity_of_PUP_main_campus_Philippines
