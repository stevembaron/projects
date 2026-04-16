const STORAGE_KEY = "utah-permit-practice-misses";

const SOURCES = {
  permit: "Utah DLD Learner Permit page",
  handbook: "Utah Driver Handbook 2025-2026",
};

const CAT_REACTIONS = [
  "Patty has entered review mode. Tiny clipboard, huge expectations.",
  "Close, but the cat is gently requesting a re-read.",
  "The whiskers say: almost, but Utah says otherwise.",
  "A noble attempt. The cat accepts your offering and points at the explanation.",
  "Not quite. Patty is not mad, just extremely invested.",
  "The answer took the scenic route. Let’s bring it back to the handbook.",
  "A small miss. The cat has seen worse parking.",
  "Patty blinked twice. That means check the rule and try again.",
];

const CAT_IMAGE = {
  src: "assets/patty-review.svg",
  alt: "A tabby cat looking serious about permit test review",
};

const QUESTION_BANK = [
  {
    id: "permit-age",
    category: "Learner Permit",
    prompt: "How old must you be to apply for a Utah learner permit?",
    answers: ["14 years old", "15 years old", "15 and a half", "16 years old"],
    correct: 1,
    explain: "Utah DLD says you must be at least 15 to apply for a learner permit.",
    source: SOURCES.permit,
  },
  {
    id: "permit-test-size",
    category: "Learner Permit",
    prompt: "The Utah learner permit written knowledge test has how many questions?",
    answers: ["25", "35", "50", "75"],
    correct: 2,
    explain: "The permit test is a 50-question closed-book written knowledge test.",
    source: SOURCES.permit,
  },
  {
    id: "permit-valid",
    category: "Learner Permit",
    prompt: "How long are Utah learner permits and written knowledge test scores valid?",
    answers: ["6 months", "12 months", "18 months", "24 months"],
    correct: 2,
    explain: "Utah lists both written knowledge test scores and learner permits as valid for 18 months.",
    source: SOURCES.permit,
  },
  {
    id: "permit-hold-15",
    category: "Learner Permit",
    prompt: "A 15-year-old Utah permit holder must hold the permit for how long before a driver license?",
    answers: ["30 days", "90 days", "6 months and until age 16", "1 year after driver education"],
    correct: 2,
    explain: "For age 15, Utah requires a 6-month holding period and the driver must be at least 16 for the license.",
    source: SOURCES.permit,
  },
  {
    id: "practice-hours",
    category: "Teen Driver",
    prompt: "How many supervised practice driving hours are required for Utah drivers under 19?",
    answers: ["20 hours, including 5 after sunset", "30 hours, including 10 after sunset", "40 hours, including 10 after sunset", "50 hours, including 15 after sunset"],
    correct: 2,
    explain: "Utah requires 40 practice hours for teen drivers, and 10 of those hours must be after sunset.",
    source: SOURCES.permit,
  },
  {
    id: "permit-supervisor-15",
    category: "Teen Driver",
    prompt: "With a Utah learner permit at age 15, who may sit in the front passenger seat while you drive?",
    answers: ["Any licensed friend age 18 or older", "A licensed parent, legal guardian, approved instructor, or properly authorized responsible adult", "Only a parent, no exceptions", "Any family member with a license"],
    correct: 1,
    explain: "Utah allows a licensed parent, legal guardian, approved instructor, responsible adult who signed financial responsibility, or an authorized person age 21+ in the front seat under the listed conditions.",
    source: SOURCES.permit,
  },
  {
    id: "permit-possession",
    category: "Learner Permit",
    prompt: "When driving with a Utah learner permit, the permit must be:",
    answers: ["Kept at home until the road test", "In your possession while driving", "Carried only on freeways", "Uploaded to a school portal"],
    correct: 1,
    explain: "Utah requires the learner permit to be in possession while driving.",
    source: SOURCES.permit,
  },
  {
    id: "under18-financial",
    category: "Teen Driver",
    prompt: "For a Utah driver under 18, who must sign for financial responsibility?",
    answers: ["The permit holder", "A parent or legal guardian", "The driving instructor", "A school administrator"],
    correct: 1,
    explain: "A parent or legal guardian must sign for financial responsibility for a minor driver under 18.",
    source: SOURCES.permit,
  },
  {
    id: "new-2025-minor-adult",
    category: "Teen Driver",
    prompt: "Under Utah's 2025 minor-driver change, if a permit holder under 18 drives with an adult who is not the parent or guardian, that adult may need:",
    answers: ["A CDL", "Evidence they are authorized by the parent or guardian", "A motorcycle endorsement", "A notarized road map"],
    correct: 1,
    explain: "The 2025 handbook update says the adult beside a minor permit holder must have evidence of authorization when the rule applies.",
    source: SOURCES.handbook,
  },
  {
    id: "class-d-age",
    category: "Licensing",
    prompt: "What is the minimum age for an original regular Utah Class D driver license?",
    answers: ["15", "15 and a half", "16", "17"],
    correct: 2,
    explain: "The handbook states that an original regular Class D license requires the applicant to be at least 16.",
    source: SOURCES.handbook,
  },
  {
    id: "utah-residency",
    category: "Licensing",
    prompt: "For a regular Utah driver license, how many Utah residency address documents are required?",
    answers: ["One", "Two", "Three", "None if you have a birth certificate"],
    correct: 1,
    explain: "The handbook lists two acceptable Utah residence address documents for a regular license or ID.",
    source: SOURCES.handbook,
  },
  {
    id: "not-accepted-docs",
    category: "Licensing",
    prompt: "At the Driver License office, documents generally must be:",
    answers: ["Original or certified copies", "Photocopied to save time", "Faxed before the appointment only", "Screenshots on a phone"],
    correct: 0,
    explain: "The handbook says documents must be original or certified copies by the issuing agency; faxed or photocopied documents are not accepted.",
    source: SOURCES.handbook,
  },
  {
    id: "vision-min",
    category: "Licensing",
    prompt: "What minimum vision standard does Utah list for an unrestricted license?",
    answers: ["20/20", "20/30", "20/40", "20/70"],
    correct: 2,
    explain: "Utah lists 20/40 or better in at least one eye as the unrestricted standard.",
    source: SOURCES.handbook,
  },
  {
    id: "written-score",
    category: "Testing",
    prompt: "What score is required to pass Utah's written knowledge test?",
    answers: ["70%", "75%", "80%", "90%"],
    correct: 2,
    explain: "The handbook says you need a score of 80% or higher on the written knowledge test.",
    source: SOURCES.handbook,
  },
  {
    id: "skills-stop",
    category: "Testing",
    prompt: "During a driving skills test, when should you make a complete stop?",
    answers: ["Only when traffic is present", "Before the stop line, crosswalk, or sidewalk", "After your front tires pass the crosswalk", "Only if the examiner says so"],
    correct: 1,
    explain: "Utah testing guidance expects a complete stop before the stop line, crosswalk, or sidewalk.",
    source: SOURCES.handbook,
  },
  {
    id: "seatbelt-law",
    category: "Safety",
    prompt: "In Utah, safety belts are required for:",
    answers: ["The driver only", "Front-seat passengers only", "The driver and all passengers", "Only people under 18"],
    correct: 2,
    explain: "Utah's handbook describes safety belt use as required for the driver and all passengers.",
    source: SOURCES.handbook,
  },
  {
    id: "child-seat-age",
    category: "Safety",
    prompt: "Children younger than what age must generally be properly restrained in an approved child safety seat in Utah?",
    answers: ["5", "6", "8", "10"],
    correct: 2,
    explain: "Utah's child restraint rule generally applies to children younger than 8, with height exceptions in the handbook.",
    source: SOURCES.handbook,
  },
  {
    id: "backing",
    category: "Basic Driving",
    prompt: "When backing a vehicle, what should you do?",
    answers: ["Rely only on the rearview camera", "Look to the rear and back slowly", "Back quickly to clear traffic", "Keep both hands at 10 and 2 without looking back"],
    correct: 1,
    explain: "The handbook emphasizes looking back and backing slowly; cameras and mirrors do not replace checking behind you.",
    source: SOURCES.handbook,
  },
  {
    id: "lane-change",
    category: "Basic Driving",
    prompt: "Before changing lanes, Utah's handbook says you should signal, check mirrors, and:",
    answers: ["Speed up first", "Make a head check over your shoulder", "Tap the brakes twice", "Honk"],
    correct: 1,
    explain: "A head check over the shoulder helps catch vehicles in the blind spot before you move.",
    source: SOURCES.handbook,
  },
  {
    id: "parallel-curb",
    category: "Basic Driving",
    prompt: "When parking on a hill facing uphill with a curb, which way should the front wheels be turned?",
    answers: ["Toward the curb", "Away from the curb", "Straight ahead", "It does not matter"],
    correct: 1,
    explain: "Facing uphill with a curb, turn the wheels away from the curb so the curb can stop the vehicle if it rolls.",
    source: SOURCES.handbook,
  },
  {
    id: "downhill-curb",
    category: "Basic Driving",
    prompt: "When parking on a hill facing downhill, which way should the wheels be turned?",
    answers: ["Toward the curb or road edge", "Away from the curb", "Straight ahead", "Only left"],
    correct: 0,
    explain: "Facing downhill, turn the wheels toward the curb or edge so the vehicle rolls away from traffic if the brake fails.",
    source: SOURCES.handbook,
  },
  {
    id: "signal-time",
    category: "Basic Driving",
    prompt: "Utah's handbook tells drivers to signal for at least how long before a turn?",
    answers: ["1 second", "2 seconds", "5 seconds", "10 seconds"],
    correct: 1,
    explain: "The handbook repeats the two-second signal rule for turns and lane-position changes.",
    source: SOURCES.handbook,
  },
  {
    id: "following-freeway",
    category: "Freeway",
    prompt: "On a freeway, Utah says you should keep at least what following distance in normal conditions?",
    answers: ["1 second", "2 seconds", "4 seconds", "8 seconds"],
    correct: 1,
    explain: "The freeway section says to maintain at least a two-second following distance, and increase it in adverse conditions.",
    source: SOURCES.handbook,
  },
  {
    id: "freeway-u-turn",
    category: "Freeway",
    prompt: "Making a U-turn on a freeway is:",
    answers: ["Allowed if traffic is stopped", "Allowed only at night", "Illegal", "Allowed from the emergency lane"],
    correct: 2,
    explain: "Utah's freeway section is direct: do not make U-turns on the freeway.",
    source: SOURCES.handbook,
  },
  {
    id: "left-lane",
    category: "Freeway",
    prompt: "If you are in the left lane on a multi-lane highway and a faster vehicle approaches from behind, you should:",
    answers: ["Stay left if you are driving the speed limit", "Move safely right to allow the vehicle to pass", "Brake to warn them", "Use the shoulder"],
    correct: 1,
    explain: "Utah warns that left-lane drivers can be cited for impeding traffic if they do not move right when approached from behind.",
    source: SOURCES.handbook,
  },
  {
    id: "express-lines",
    category: "Freeway",
    prompt: "In Utah express/carpool lanes, crossing a double white line is:",
    answers: ["Allowed to pass", "Allowed near any exit", "Illegal", "Required before every interchange"],
    correct: 2,
    explain: "The handbook says moving in and out of the express lane is not allowed across double white lines; use marked access points.",
    source: SOURCES.handbook,
  },
  {
    id: "flex-lane",
    category: "Rules of Road",
    prompt: "A green arrow over a flex lane means:",
    answers: ["You may use that lane", "You must leave that lane", "The lane is for buses only", "The lane is closed ahead"],
    correct: 0,
    explain: "For flex lanes, overhead signals control use: green arrow means the lane may be used, red X means it may not.",
    source: SOURCES.handbook,
  },
  {
    id: "four-way",
    category: "Right-of-Way",
    prompt: "At a four-way stop, if two vehicles arrive at the same time, who should yield?",
    answers: ["The driver on the left yields to the driver on the right", "The driver on the right yields to the driver on the left", "The larger vehicle always goes first", "Whoever waves first goes first"],
    correct: 0,
    explain: "Utah's right-of-way list says to yield to the driver on your right if both arrive at the same time.",
    source: SOURCES.handbook,
  },
  {
    id: "left-turn-yield",
    category: "Right-of-Way",
    prompt: "When turning left, you must yield to:",
    answers: ["Only pedestrians", "Drivers in the opposite lane", "Vehicles behind you only", "No one if you signaled"],
    correct: 1,
    explain: "A driver turning left yields to oncoming drivers in the opposite lane.",
    source: SOURCES.handbook,
  },
  {
    id: "driveway-yield",
    category: "Right-of-Way",
    prompt: "When entering a public road from a driveway or private road, you should yield to:",
    answers: ["Drivers already on the public road", "Only buses", "Only drivers turning left", "No one"],
    correct: 0,
    explain: "The handbook says drivers coming from a driveway or private road yield to drivers on the public road.",
    source: SOURCES.handbook,
  },
  {
    id: "yield-sign",
    category: "Signs",
    prompt: "A yield sign means you must:",
    answers: ["Stop every time", "Slow down and yield to traffic with the right-of-way", "Speed up to merge", "Turn right only"],
    correct: 1,
    explain: "A yield sign means slow down and yield to traffic that has the right-of-way; stop if needed.",
    source: SOURCES.handbook,
  },
  {
    id: "warning-shape",
    category: "Signs",
    prompt: "Warning signs are usually:",
    answers: ["Blue rectangles", "Diamond shaped and yellow with black letters or symbols", "Red octagons", "Green circles"],
    correct: 1,
    explain: "Utah's sign section describes warning signs as usually diamond-shaped and yellow with black letters or symbols.",
    source: SOURCES.handbook,
  },
  {
    id: "regulatory-signs",
    category: "Signs",
    prompt: "Regulatory signs usually tell drivers about:",
    answers: ["Traffic directions, lane use, turns, speed, and parking", "Scenic routes only", "Weather reports", "Gas prices"],
    correct: 0,
    explain: "Regulatory signs control legal movements and road use, including speed, parking, turns, and lanes.",
    source: SOURCES.handbook,
  },
  {
    id: "railroad-round",
    category: "Signs",
    prompt: "A round yellow sign with an X and RR warns you to:",
    answers: ["Prepare for a railroad crossing", "Enter a roundabout", "Use a carpool lane", "Expect a school zone only"],
    correct: 0,
    explain: "The round yellow RR warning sign means a railroad crossing is ahead: slow down, look, listen, and be ready to stop.",
    source: SOURCES.handbook,
  },
  {
    id: "flashing-red",
    category: "Traffic Signals",
    prompt: "A flashing red traffic light should be treated like:",
    answers: ["A green light", "A stop sign", "A yield sign only", "A warning to speed up"],
    correct: 1,
    explain: "The handbook's signal rules treat a flashing red light like a stop sign: stop, then proceed when safe.",
    source: SOURCES.handbook,
  },
  {
    id: "flashing-yellow",
    category: "Traffic Signals",
    prompt: "A flashing yellow traffic light means:",
    answers: ["Stop and wait for green", "Proceed with caution", "The road is closed", "Only bicycles may go"],
    correct: 1,
    explain: "A flashing yellow light means proceed with caution after checking traffic and pedestrians.",
    source: SOURCES.handbook,
  },
  {
    id: "yellow-arrow",
    category: "Traffic Signals",
    prompt: "A flashing yellow left-turn arrow means the turn is:",
    answers: ["Protected from oncoming traffic", "Permitted, but you must yield", "Illegal", "Only for emergency vehicles"],
    correct: 1,
    explain: "A flashing yellow arrow allows the turn after yielding to oncoming traffic and pedestrians.",
    source: SOURCES.handbook,
  },
  {
    id: "school-bus-red",
    category: "School Bus",
    prompt: "When a school bus has alternating flashing red lights, traffic generally must:",
    answers: ["Slow to 20 mph and pass", "Stop before reaching the bus", "Pass only on the left", "Continue if no children are visible"],
    correct: 1,
    explain: "Flashing red school bus lights mean stop before reaching the bus and stay stopped until the lights stop and it is safe.",
    source: SOURCES.handbook,
  },
  {
    id: "school-bus-divided",
    category: "School Bus",
    prompt: "On a divided highway with a physical median, drivers traveling the opposite direction from a stopped school bus usually:",
    answers: ["Must stop in every case", "May proceed with caution", "Must honk before passing", "Must turn around"],
    correct: 1,
    explain: "Utah's school bus rules distinguish divided highways; opposite-direction traffic separated by a median may proceed cautiously.",
    source: SOURCES.handbook,
  },
  {
    id: "speed-school",
    category: "Speed",
    prompt: "What is Utah's default speed limit in a school zone unless otherwise posted?",
    answers: ["15 mph", "20 mph", "25 mph", "30 mph"],
    correct: 1,
    explain: "Utah lists 20 mph as the school zone default speed unless posted otherwise.",
    source: SOURCES.handbook,
  },
  {
    id: "speed-residential",
    category: "Speed",
    prompt: "What is Utah's default speed limit in residential areas unless otherwise posted?",
    answers: ["20 mph", "25 mph", "30 mph", "35 mph"],
    correct: 1,
    explain: "Utah lists 25 mph as the default for residential areas unless another limit is posted.",
    source: SOURCES.handbook,
  },
  {
    id: "speed-urban",
    category: "Speed",
    prompt: "What is Utah's default speed limit in business areas unless otherwise posted?",
    answers: ["20 mph", "25 mph", "30 mph", "40 mph"],
    correct: 1,
    explain: "The Utah handbook lists 25 mph in business or residential areas unless another limit is posted.",
    source: SOURCES.handbook,
  },
  {
    id: "basic-speed",
    category: "Speed",
    prompt: "Utah's basic speed rule means you must:",
    answers: ["Always drive exactly the posted speed", "Drive at a speed reasonable and prudent for conditions", "Drive 5 mph under the limit at all times", "Match the fastest traffic"],
    correct: 1,
    explain: "The posted limit is not a promise that the speed is safe. You must adjust for traffic, weather, visibility, and road conditions.",
    source: SOURCES.handbook,
  },
  {
    id: "roundabout",
    category: "Intersections",
    prompt: "When entering a roundabout, you should:",
    answers: ["Slow down, yield, and enter when clear", "Stop inside the circle", "Enter beside large trucks", "Drive clockwise"],
    correct: 0,
    explain: "Utah's roundabout guidance says to slow down, yield to traffic and pedestrians, then enter when clear.",
    source: SOURCES.handbook,
  },
  {
    id: "dui-bac",
    category: "Alcohol & Drugs",
    prompt: "Utah's per se blood alcohol concentration limit for most drivers is:",
    answers: ["0.03", "0.05", "0.08", "0.10"],
    correct: 1,
    explain: "Utah's DUI law uses a .05 blood alcohol concentration standard for most drivers.",
    source: SOURCES.handbook,
  },
  {
    id: "under21-alcohol",
    category: "Alcohol & Drugs",
    prompt: "For a driver under 21 in Utah, alcohol rules are best summarized as:",
    answers: ["One drink is legal if a parent is present", "Any measurable alcohol can cause license action", "The .05 limit does not apply", "Only beer is restricted"],
    correct: 1,
    explain: "Utah has strict under-21 alcohol rules; any measurable alcohol can lead to consequences.",
    source: SOURCES.handbook,
  },
  {
    id: "implied-consent",
    category: "Alcohol & Drugs",
    prompt: "Utah's implied consent law means that by driving, you have agreed to:",
    answers: ["Let police search your phone", "Take a chemical test when lawfully requested for alcohol or drugs", "Buy state insurance", "Drive only during daylight"],
    correct: 1,
    explain: "Implied consent laws connect the privilege to drive with chemical testing when an officer has legal grounds.",
    source: SOURCES.handbook,
  },
  {
    id: "phone-under18",
    category: "Distractions",
    prompt: "A Utah driver under 18 may use a handheld wireless device while driving only for limited reasons such as:",
    answers: ["Changing music", "Any hands-free call", "A medical emergency, safety hazard, criminal activity, or communicating with a parent/legal guardian", "Looking up directions at a stoplight"],
    correct: 2,
    explain: "The handbook lists narrow exceptions for drivers under 18, including emergencies, hazards, criminal activity, or communicating with a parent or guardian.",
    source: SOURCES.handbook,
  },
  {
    id: "texting",
    category: "Distractions",
    prompt: "While operating a moving vehicle on a Utah highway, manually reading or sending a text is:",
    answers: ["Allowed under 25 mph", "Allowed at red lights only", "Not allowed", "Allowed if one hand stays on the wheel"],
    correct: 2,
    explain: "Utah law prohibits manually writing, sending, or reading written communication while operating a moving motor vehicle.",
    source: SOURCES.handbook,
  },
  {
    id: "work-zone-fines",
    category: "Work Zones",
    prompt: "In Utah work zones, speeding fines are:",
    answers: ["Waived for new drivers", "Doubled", "Half the normal amount", "Only warnings"],
    correct: 1,
    explain: "The handbook says fines for speeding in a work zone are doubled.",
    source: SOURCES.handbook,
  },
  {
    id: "flagger",
    category: "Work Zones",
    prompt: "If a flagger directs traffic in a work zone, you must:",
    answers: ["Follow the flagger's directions", "Follow only posted signs", "Ignore them if the light is green", "Stop only for police"],
    correct: 0,
    explain: "Utah's work-zone section says drivers must do as the flagger directs.",
    source: SOURCES.handbook,
  },
  {
    id: "flood-six",
    category: "Weather",
    prompt: "About how much water can reach the bottom of most passenger cars and cause loss of control or stalling?",
    answers: ["2 inches", "6 inches", "18 inches", "4 feet"],
    correct: 1,
    explain: "The handbook warns that six inches of water can reach the bottom of most passenger cars and cause control problems or stalling.",
    source: SOURCES.handbook,
  },
  {
    id: "flood-two-feet",
    category: "Weather",
    prompt: "About how much moving water can carry away most vehicles, including SUVs and pickups?",
    answers: ["6 inches", "1 foot", "2 feet", "5 feet"],
    correct: 2,
    explain: "Utah's handbook warns that two feet of moving water can carry away most vehicles.",
    source: SOURCES.handbook,
  },
  {
    id: "fatigue-break",
    category: "Fatigue",
    prompt: "On long trips, Utah's handbook recommends planning a break about every:",
    answers: ["Hour", "Two hours", "Four hours", "Six hours"],
    correct: 1,
    explain: "The fatigue section recommends stopping every two hours during long trips.",
    source: SOURCES.handbook,
  },
  {
    id: "desert-breakdown",
    category: "Weather",
    prompt: "If your vehicle breaks down in the desert, Utah's handbook says you should generally:",
    answers: ["Stay with the vehicle", "Walk until you find shade", "Leave the road immediately", "Drain the radiator"],
    correct: 0,
    explain: "The desert-driving section says to stay with the vehicle unless help is visibly within a few minutes' walk.",
    source: SOURCES.handbook,
  },
  {
    id: "emergency-vehicle",
    category: "Emergency Vehicles",
    prompt: "When an emergency vehicle approaches with sirens or flashing lights, you must:",
    answers: ["Speed up to get ahead", "Drive at once to the right side of the road and stop", "Stop in the left lane", "Follow closely"],
    correct: 1,
    explain: "Utah requires drivers to yield, move to the right side of the road, and stop until the emergency vehicle has passed.",
    source: SOURCES.handbook,
  },
  {
    id: "fire-vehicle-distance",
    category: "Emergency Vehicles",
    prompt: "Unless on official business, you may not follow within what distance of a fire vehicle responding to an alarm?",
    answers: ["100 feet", "250 feet", "500 feet", "1,000 feet"],
    correct: 2,
    explain: "The handbook says not to follow within 500 feet of a fire vehicle responding to an alarm.",
    source: SOURCES.handbook,
  },
  {
    id: "move-over",
    category: "Emergency Vehicles",
    prompt: "Utah's move over law says when approaching a stationary roadside vehicle with flashing lights, you should slow down and, when practical:",
    answers: ["Change lanes away from it", "Honk twice", "Stop next to it", "Drive on the shoulder"],
    correct: 0,
    explain: "Drivers should reduce speed, give as much space as practical, and change lanes away when safe and practical.",
    source: SOURCES.handbook,
  },
  {
    id: "truck-no-zone",
    category: "Sharing Road",
    prompt: "Large trucks have bigger blind spots. A good rule is:",
    answers: ["If you cannot see the truck driver in the mirror, the driver probably cannot see you", "Stay directly behind the trailer", "Pass on the right before turns", "Brake hard in front of the truck"],
    correct: 0,
    explain: "The handbook warns about truck blind spots; staying visible and out of no-zones reduces crash risk.",
    source: SOURCES.handbook,
  },
  {
    id: "bike-rights",
    category: "Sharing Road",
    prompt: "On Utah roads, bicycle operators generally:",
    answers: ["May ignore traffic laws", "Have the same rights and duties as motor vehicle operators", "Must always ride on sidewalks", "Can ride against traffic"],
    correct: 1,
    explain: "The handbook introduction says bicycle operators must obey rules of the road and have the same rights and duties as motor vehicle operators.",
    source: SOURCES.handbook,
  },
  {
    id: "crash-injury",
    category: "Crashes",
    prompt: "If you are involved in a crash with injury, death, or property damage, a key first step is to:",
    answers: ["Leave if your car still moves", "Stop immediately and render reasonable assistance", "Post about it online", "Move the other driver's vehicle yourself"],
    correct: 1,
    explain: "Utah's crash guidance requires stopping and helping as reasonably needed after a crash.",
    source: SOURCES.handbook,
  },
  {
    id: "insurance",
    category: "Crashes",
    prompt: "Utah vehicle owners must generally maintain:",
    answers: ["No-fault insurance", "Only collision insurance", "Only roadside assistance", "Insurance only for freeway driving"],
    correct: 0,
    explain: "Utah is a no-fault state and the handbook includes required insurance guidance for registered vehicles.",
    source: SOURCES.handbook,
  },
  {
    id: "points-under21",
    category: "Driver Record",
    prompt: "Utah drivers under 21 face driver review action at how many points?",
    answers: ["35", "50", "70", "200"],
    correct: 2,
    explain: "Utah's point system uses a lower threshold for drivers under 21; 70 points can trigger action.",
    source: SOURCES.handbook,
  },
  {
    id: "points-adult",
    category: "Driver Record",
    prompt: "Utah drivers 21 and older face driver review action at how many points?",
    answers: ["70", "100", "150", "200"],
    correct: 3,
    explain: "For drivers 21 and older, Utah's point system threshold is 200 points within the listed period.",
    source: SOURCES.handbook,
  },
  {
    id: "organ-donor",
    category: "Licensing",
    prompt: "Utah driver license services include an option related to:",
    answers: ["Organ donor registration", "Airport precheck", "Fishing licenses only", "Vehicle title transfer only"],
    correct: 0,
    explain: "The Driver License Division services include organ donor registration during licensing services.",
    source: SOURCES.handbook,
  },
];

const elements = {
  answeredCount: document.getElementById("answeredCount"),
  correctCount: document.getElementById("correctCount"),
  streakCount: document.getElementById("streakCount"),
  modeSelect: document.getElementById("modeSelect"),
  startBtn: document.getElementById("startBtn"),
  missedBtn: document.getElementById("missedBtn"),
  modeNote: document.getElementById("modeNote"),
  categoryPill: document.getElementById("categoryPill"),
  questionProgress: document.getElementById("questionProgress"),
  progressBar: document.getElementById("progressBar"),
  questionText: document.getElementById("questionText"),
  answers: document.getElementById("answers"),
  feedback: document.getElementById("feedback"),
  skipBtn: document.getElementById("skipBtn"),
  nextBtn: document.getElementById("nextBtn"),
  focusList: document.getElementById("focusList"),
};

let session = {
  questions: [],
  index: 0,
  answered: 0,
  correct: 0,
  streak: 0,
  locked: false,
  chosen: null,
};

function init() {
  elements.startBtn.addEventListener("click", () => startSession(elements.modeSelect.value));
  elements.missedBtn.addEventListener("click", startMissedSession);
  elements.skipBtn.addEventListener("click", skipQuestion);
  elements.nextBtn.addEventListener("click", nextQuestion);
  elements.modeSelect.addEventListener("change", updateModeNote);
  updateModeNote();
  renderFocus();
  startSession("exam");
}

function updateModeNote() {
  const mode = elements.modeSelect.value;
  const copy = {
    exam: "A full run uses 50 random questions. Passing target: 40 correct.",
    quick: "Ten-question drill for a fast confidence check.",
    weak: "A shorter set from categories that are commonly tricky on permit tests.",
  };
  elements.modeNote.textContent = copy[mode];
}

function startSession(mode) {
  const pool = mode === "weak" ? weightedTroublePool() : [...QUESTION_BANK];
  const count = mode === "quick" ? 10 : 50;
  session = {
    questions: shuffle(pool).slice(0, Math.min(count, pool.length)),
    index: 0,
    answered: 0,
    correct: 0,
    streak: 0,
    locked: false,
    chosen: null,
  };
  renderQuestion();
}

function startMissedSession() {
  const missed = readMisses();
  const questions = QUESTION_BANK.filter((question) => missed.includes(question.id));
  if (!questions.length) {
    elements.feedback.className = "feedback good";
    elements.feedback.innerHTML = "<strong>No missed questions saved.</strong>Miss a question and it will land here for targeted review.";
    return;
  }
  session = {
    questions: shuffle(questions),
    index: 0,
    answered: 0,
    correct: 0,
    streak: 0,
    locked: false,
    chosen: null,
  };
  renderQuestion();
}

function weightedTroublePool() {
  const trouble = new Set(["Teen Driver", "Speed", "Traffic Signals", "Right-of-Way", "School Bus", "Alcohol & Drugs", "Distractions"]);
  return QUESTION_BANK.filter((question) => trouble.has(question.category));
}

function renderQuestion() {
  const question = session.questions[session.index];
  if (!question) {
    renderSummary();
    return;
  }

  session.locked = false;
  session.chosen = null;
  elements.categoryPill.textContent = question.category;
  elements.questionProgress.textContent = `Question ${session.index + 1} of ${session.questions.length}`;
  elements.progressBar.style.width = `${(session.index / session.questions.length) * 100}%`;
  elements.questionText.textContent = question.prompt;
  elements.answers.innerHTML = "";
  elements.feedback.className = "feedback hidden";
  elements.nextBtn.disabled = true;
  elements.skipBtn.disabled = false;

  question.answers.forEach((answer, index) => {
    const button = document.createElement("button");
    button.className = "answer-btn";
    button.type = "button";
    button.textContent = answer;
    button.addEventListener("click", () => chooseAnswer(index));
    elements.answers.append(button);
  });

  updateStats();
  renderFocus();
}

function chooseAnswer(index) {
  if (session.locked) return;
  const question = session.questions[session.index];
  const isCorrect = index === question.correct;
  const buttons = [...elements.answers.querySelectorAll(".answer-btn")];

  session.locked = true;
  session.chosen = index;
  session.answered += 1;
  session.correct += isCorrect ? 1 : 0;
  session.streak = isCorrect ? session.streak + 1 : 0;

  buttons.forEach((button, buttonIndex) => {
    button.disabled = true;
    if (buttonIndex === question.correct) button.classList.add("correct");
    if (buttonIndex === index && !isCorrect) button.classList.add("wrong");
  });

  if (isCorrect) {
    removeMiss(question.id);
  } else {
    addMiss(question.id);
  }

  const catReaction = CAT_REACTIONS[(session.answered + session.index) % CAT_REACTIONS.length];
  const wrongFeedback = `
    <div class="cat-reaction">
      <img src="${CAT_IMAGE.src}" alt="${CAT_IMAGE.alt}" />
      <p>${catReaction}</p>
    </div>
  `;

  elements.feedback.className = `feedback ${isCorrect ? "good" : "bad"}`;
  elements.feedback.innerHTML = `
    <strong>${isCorrect ? "Correct." : "Not this one."}</strong>
    ${isCorrect ? "" : wrongFeedback}
    ${question.explain}
    <div class="fine-print">Source: ${question.source}</div>
  `;
  elements.nextBtn.disabled = false;
  elements.skipBtn.disabled = true;
  updateStats();
  renderFocus();
}

function skipQuestion() {
  if (session.locked) return;
  session.questions.push(session.questions.splice(session.index, 1)[0]);
  renderQuestion();
}

function nextQuestion() {
  session.index += 1;
  renderQuestion();
}

function renderSummary() {
  const score = session.correct;
  const total = session.questions.length;
  const percent = total ? Math.round((score / total) * 100) : 0;
  const passLine = total === 50 ? "Utah's practice target here is 40 out of 50." : "Run the full 50 when she is warm.";
  const message = total === 50 && score >= 40 ? "That is a passing pace." : score === total ? "Perfect run." : "Good data. Now drill the misses.";

  elements.categoryPill.textContent = "Finished";
  elements.questionProgress.textContent = `${score}/${total} correct`;
  elements.progressBar.style.width = "100%";
  elements.questionText.textContent = `${percent}% - ${message}`;
  elements.answers.innerHTML = "";
  elements.feedback.className = "feedback";
  elements.feedback.innerHTML = `
    <strong>${passLine}</strong>
    Missed questions are saved automatically. Use “Retry missed” to make the weak spots boring.
  `;
  elements.nextBtn.disabled = true;
  elements.skipBtn.disabled = true;
  updateStats();
  renderFocus();
}

function updateStats() {
  elements.answeredCount.textContent = session.answered;
  elements.correctCount.textContent = session.correct;
  elements.streakCount.textContent = session.streak;
}

function renderFocus() {
  const misses = readMisses();
  const missedQuestions = QUESTION_BANK.filter((question) => misses.includes(question.id));
  const counts = missedQuestions.reduce((acc, question) => {
    acc[question.category] = (acc[question.category] || 0) + 1;
    return acc;
  }, {});
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 4);

  if (!entries.length) {
    elements.focusList.innerHTML = `
      <div class="focus-item">
        <strong>No saved weak spots yet.</strong>
        Answer a few questions and this will turn into a short study map.
      </div>
    `;
    return;
  }

  elements.focusList.innerHTML = entries
    .map(([category, count]) => {
      const noun = count === 1 ? "miss" : "misses";
      return `<div class="focus-item"><strong>${category}</strong>${count} saved ${noun}</div>`;
    })
    .join("");
}

function readMisses() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function addMiss(id) {
  const misses = new Set(readMisses());
  misses.add(id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...misses]));
}

function removeMiss(id) {
  const misses = readMisses().filter((miss) => miss !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(misses));
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
  }
  return copy;
}

init();
