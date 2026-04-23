const EXAM_DATE = new Date("2026-05-05T08:00:00");
const STORAGE_KEY = "aphug-prep-stats-v2";

const BIG_IDEAS = [
  {
    code: "PSO",
    title: "Patterns and Spatial Organization",
    summary:
      "Human society is arranged in spatial patterns shaped by political, historical, cultural, and economic factors.",
  },
  {
    code: "IMP",
    title: "Impacts and Interactions",
    summary:
      "People, environments, and historical or contemporary actions affect one another through cause-and-effect relationships.",
  },
  {
    code: "SPS",
    title: "Spatial Processes and Societal Change",
    summary:
      "A spatial perspective helps explain how places connect, change, and produce environmental and social consequences.",
  },
];

const SKILLS = [
  {
    code: "1",
    title: "Concepts and Processes",
    summary: "Explain and compare geographic concepts, processes, models, and theories.",
  },
  {
    code: "2",
    title: "Spatial Relationships",
    summary: "Analyze patterns, networks, relationships, and outcomes in real contexts.",
  },
  {
    code: "3",
    title: "Data Analysis",
    summary: "Interpret quantitative geographic data in maps, charts, tables, graphs, and infographics.",
  },
  {
    code: "4",
    title: "Source Analysis",
    summary: "Read visual or written sources closely, compare patterns, and note limits in what they show.",
  },
  {
    code: "5",
    title: "Scale Analysis",
    summary: "Use local, regional, national, and global scales to explain spatial relationships.",
  },
];

const FRQ_CARDS = [
  {
    title: "FRQ 1",
    chip: "No stimulus",
    notes: [
      "Read the scenario carefully before you write.",
      "Underline the task verbs: describe, explain, compare, apply.",
      "Answer every part in order and use precise geographic language.",
    ],
  },
  {
    title: "FRQ 2",
    chip: "One stimulus",
    notes: [
      "Identify exactly what the map, image, or data source shows.",
      "Pull evidence from the stimulus before you explain the pattern.",
      "Connect the evidence to a model, process, or concept from the unit.",
    ],
  },
  {
    title: "FRQ 3",
    chip: "Two stimuli",
    notes: [
      "Compare what each source shows before jumping to conclusions.",
      "Look for scale: local, regional, national, or global relationships.",
      "Explain how the sources support a larger geographic argument together.",
    ],
  },
];

const UNITS = [
  {
    id: "unit-1",
    short: "Unit 1",
    title: "Thinking Geographically",
    weight: "8%–10%",
    summary:
      "Focuses on the tools and methods geographers use to study places, patterns, and regions.",
    topics: [
      "Different types of maps and what they tell you",
      "How geographers collect and use data",
      "Spatial relationships and patterns",
      "Data analysis at different scales",
      "How geographers define regions",
    ],
    officialTopics: ["1.1 Introduction to Maps", "1.4 Spatial Concepts", "1.7 Regional Analysis"],
  },
  {
    id: "unit-2",
    short: "Unit 2",
    title: "Population and Migration Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Explores how population patterns, demographic theories, and migration shape places and societies.",
    topics: [
      "Population density and how it affects society and the environment",
      "Theories of population growth and decline",
      "Population and immigration policies and their effects",
      "The causes and effects of migration",
    ],
    officialTopics: ["2.5 The Demographic Transition Model", "2.7 Population Policies", "2.12 Effects of Migration"],
  },
  {
    id: "unit-3",
    short: "Unit 3",
    title: "Cultural Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Studies how culture spreads, changes, and leaves visible marks on landscapes.",
    topics: [
      "The different ways that cultural practices spread",
      "Historical forces such as colonialism and trade",
      "Modern forces such as globalization",
      "Why different religions spread in different ways",
    ],
    officialTopics: ["3.2 Cultural Landscapes", "3.5 Historical Causes of Diffusion", "3.8 Effects of Diffusion"],
  },
  {
    id: "unit-4",
    short: "Unit 4",
    title: "Political Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Looks at states, nations, boundaries, governance, and forces that challenge sovereignty.",
    topics: [
      "Types of political entities such as nations and nation-states",
      "The ideas and forces that shaped political boundaries",
      "Forms of government such as unitary and federal states",
      "The factors that lead to states breaking apart",
    ],
    officialTopics: ["4.1 Introduction to Political Geography", "4.5 The Function of Political Boundaries", "4.9 Challenges to Sovereignty"],
  },
  {
    id: "unit-5",
    short: "Unit 5",
    title: "Agriculture and Rural Land-Use Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Covers agricultural origins, diffusion, land use, production systems, and environmental impacts.",
    topics: [
      "How physical geography influences farming practices",
      "The origins and spread of agriculture",
      "The Green Revolution",
      "How farming practices affect the environment and society",
    ],
    officialTopics: ["5.3 Agricultural Origins and Diffusions", "5.8 Von Thunen Model", "5.11 Challenges of Contemporary Agriculture"],
  },
  {
    id: "unit-6",
    short: "Unit 6",
    title: "Cities and Urban Land-Use Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Examines urbanization, city structure, infrastructure, and sustainability in a global context.",
    topics: [
      "The factors that drive the growth of cities and suburbs",
      "Globalization and cities",
      "City infrastructure",
      "Urban design initiatives and practices",
    ],
    officialTopics: ["6.1 The Origin and Influences of Urbanization", "6.3 Cities and Globalization", "6.8 Urban Sustainability"],
  },
  {
    id: "unit-7",
    short: "Unit 7",
    title: "Industrial and Economic Development Patterns and Processes",
    weight: "12%–17%",
    summary:
      "Explains industrialization, development, trade, and changing economic patterns across places.",
    topics: [
      "The Industrial Revolution",
      "Economic sectors and patterns",
      "How economic development affects the roles of women",
      "Trade and the world economy",
    ],
    officialTopics: ["7.1 The Industrial Revolution", "7.5 Theories of Development", "7.8 Sustainable Development"],
  },
];

const FLASHCARDS = [
  { front: "Site", back: "Site explains a place using its physical characteristics such as water, terrain, or a natural harbor." },
  { front: "Situation", back: "Situation explains a place by its relative location to routes, markets, neighbors, and other places." },
  { front: "DTM Stage 2", back: "Death rates fall while birth rates stay high, so population grows quickly." },
  { front: "Relocation diffusion", back: "A cultural trait spreads because people move and carry it to a new place." },
  { front: "Contagious diffusion", back: "A trait spreads rapidly through close contact across nearby places or people." },
  { front: "Unitary state", back: "Political power is concentrated mainly in the central government." },
  { front: "Federal state", back: "Political power is shared between national and regional governments." },
  { front: "Green Revolution", back: "Improved seeds, irrigation, and fertilizer raise crop yields in many regions." },
  { front: "Bid-rent theory", back: "Land values are usually highest closest to the central business district." },
  { front: "Gentrification", back: "Reinvestment in older urban neighborhoods often raises costs and can displace residents." },
];

const SOURCES = [
  {
    label: "AP Students: AP Human Geography course page",
    url: "https://apstudents.collegeboard.org/courses/ap-human-geography",
    note: "Official unit descriptions, unit weighting, and student-facing course overview.",
  },
  {
    label: "AP Students: AP Human Geography assessment page",
    url: "https://apstudents.collegeboard.org/courses/ap-human-geography/assessment",
    note: "Official 2026 exam date, digital format, duration, and section structure.",
  },
  {
    label: "AP Central: AP Human Geography Course and Exam Description",
    url: "https://apcentral.collegeboard.org/media/pdf/ap-human-geography-course-and-exam-description.pdf?course=ap-human-geography%2F",
    note: "Official big ideas, course skills, and detailed topic names used in the atlas.",
  },
  {
    label: "AP Central: AP Human Geography Course at a Glance",
    url: "https://apcentral.collegeboard.org/media/pdf/ap-human-geography-course-at-a-glance.pdf",
    note: "Official unit pacing and topic sequence for quick review.",
  },
  {
    label: "AP Central: AP Human Geography CED clarifications and corrections",
    url: "https://apcentral.collegeboard.org/media/pdf/ap-human-geography-course-and-exam-description-clarifications.pdf",
    note: "Used as a check that no newer clarification changed the content summarized here.",
  },
];

const QUIZ_BANK = {
  scenarios: [
    {
      tag: "Scenarios",
      type: "Choose the concept",
      question:
        "A city's original location is best explained by its natural harbor, fresh water, and defensible coastline. Which concept fits best?",
      answers: ["Site factors", "Situation factors", "Relocation diffusion", "Bid-rent theory"],
      correct: 0,
      explain:
        "Site refers to the physical characteristics of a place, such as a natural harbor or water source.",
    },
    {
      tag: "Scenarios",
      type: "Choose the model",
      question:
        "A country has rapidly falling death rates, still-high birth rates, and very fast population growth. Which model stage does that pattern best match?",
      answers: ["Demographic Transition Model Stage 1", "Stage 2", "Stage 3", "Stage 4"],
      correct: 1,
      explain:
        "Stage 2 is associated with falling death rates while birth rates remain high, producing rapid population growth.",
    },
    {
      tag: "Scenarios",
      type: "Choose the process",
      question:
        "A language spreads to a new region because migrants move there and bring it with them. Which diffusion process best fits?",
      answers: ["Contagious diffusion", "Hierarchical diffusion", "Relocation diffusion", "Reverse hierarchical diffusion"],
      correct: 2,
      explain:
        "Relocation diffusion happens when people move and carry cultural traits such as language or religion to a new place.",
    },
    {
      tag: "Scenarios",
      type: "Choose the government form",
      question:
        "Most authority is concentrated in one central government, and regional governments have limited independent power. Which political structure is this?",
      answers: ["Federal state", "Unitary state", "Multinational state", "Nation-state"],
      correct: 1,
      explain:
        "A unitary state concentrates power in the national government rather than dividing it constitutionally across regions.",
    },
    {
      tag: "Scenarios",
      type: "Choose the urban process",
      question:
        "Higher-income residents move into an older inner-city neighborhood, housing values rise, and some longtime residents are priced out. Which process best fits?",
      answers: ["Suburbanization", "Gentrification", "Redistricting", "Agglomeration"],
      correct: 1,
      explain:
        "Gentrification refers to reinvestment and rising prices in older neighborhoods, often with displacement effects.",
    },
    {
      tag: "Scenarios",
      type: "Choose the land-use model",
      question:
        "Farms closest to a large city focus on dairy and vegetables because those goods spoil quickly and transport costs matter. Which model best fits?",
      answers: ["Demographic Transition Model", "Gravity model", "Von Thunen model", "Core-periphery model"],
      correct: 2,
      explain:
        "The von Thunen model predicts more intensive, perishable agriculture closer to the market.",
    },
  ],
  models: [
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "Which example best matches the Green Revolution?",
      answers: [
        "Farmers switching from crops to tourism",
        "Higher crop yields from improved seeds, irrigation, and fertilizer",
        "A religion spreading from one city to nearby villages",
        "Factories moving from cities to suburbs",
      ],
      correct: 1,
      explain:
        "The Green Revolution is associated with higher-yield seeds plus intensified use of irrigation, fertilizer, and related inputs.",
    },
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "Which pattern best fits bid-rent theory?",
      answers: [
        "Land values are highest near the central business district and decline outward",
        "Birth rates fall first, then death rates fall later",
        "Political power is evenly divided among neighborhoods",
        "Agricultural output is always highest far from urban markets",
      ],
      correct: 0,
      explain:
        "Bid-rent theory explains why land closest to the CBD is usually most expensive because accessibility is high.",
    },
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "Which example best fits a federal state?",
      answers: [
        "Regional governments hold power delegated only temporarily by the center",
        "Power is constitutionally shared between national and regional governments",
        "A state includes multiple ethnic groups",
        "One nation matches one state exactly",
      ],
      correct: 1,
      explain:
        "Federal systems divide authority between national and regional levels rather than concentrating it in one center.",
    },
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "Which job grouping belongs most directly to the tertiary sector?",
      answers: [
        "Mining and logging",
        "Auto assembly and steel production",
        "Banking, retail, and health care",
        "Subsistence farming and herding",
      ],
      correct: 2,
      explain:
        "The tertiary sector is the service sector, including activities such as finance, retail, and health care.",
    },
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "A disease spreads quickly from person to person through close contact in neighboring locations. Which diffusion type best fits?",
      answers: ["Contagious diffusion", "Relocation diffusion", "Hierarchical diffusion", "Stimulus diffusion"],
      correct: 0,
      explain:
        "Contagious diffusion spreads rapidly through direct contact across nearby places or people.",
    },
    {
      tag: "Models",
      type: "Apply the concept",
      question:
        "Which example is mainly about situation rather than site?",
      answers: [
        "A city has fertile soil and a river",
        "A city sits near major trade routes and a large market",
        "A settlement has a protected bay",
        "A village has nearby building stone",
      ],
      correct: 1,
      explain:
        "Situation refers to a place's relative location, including access to routes, markets, and surrounding places.",
    },
  ],
  reasoning: [
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "A country adopts a policy intended to reduce family size because leaders are concerned about rapid population growth. Which claim best explains the policy goal?",
      answers: [
        "The state wants to increase the crude birth rate",
        "The state wants to reduce the rate of natural increase",
        "The state wants to encourage relocation diffusion",
        "The state wants to increase suburbanization",
      ],
      correct: 1,
      explain:
        "Population policies aimed at lowering births are generally trying to slow the rate of natural increase.",
    },
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "A country exports mostly raw materials and relies heavily on extracting natural resources. Which inference is strongest?",
      answers: [
        "Its economy is weighted toward the primary sector",
        "Its economy is dominated by tertiary services",
        "Its economy has fully deindustrialized",
        "Its population is in Demographic Transition Model Stage 4",
      ],
      correct: 0,
      explain:
        "Extraction of raw materials belongs to the primary sector of the economy.",
    },
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "A former colony still uses the colonizer's language widely in government and education. Which broad explanation is most likely?",
      answers: [
        "Agricultural intensification",
        "Historical diffusion shaped by colonialism",
        "Bid-rent theory",
        "Environmental determinism",
      ],
      correct: 1,
      explain:
        "The AP course explicitly connects cultural patterns to historical forces such as colonialism and trade.",
    },
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "A city's population grows rapidly after transportation networks improve and commuting becomes easier. Which process is most directly involved?",
      answers: [
        "Urbanization and suburbanization shaped by transportation change",
        "Aging populations",
        "Stimulus diffusion of religion",
        "Devolution from the core state",
      ],
      correct: 0,
      explain:
        "The CED links urbanization and suburbanization to transportation and communication change.",
    },
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "A map shows high housing costs near the CBD and lower land values farther from the center. Which urban idea would best help explain the pattern?",
      answers: ["Bid-rent theory", "Demographic momentum", "Relocation diffusion", "Nation-state"],
      correct: 0,
      explain:
        "Bid-rent theory is used to explain why the most accessible central land often commands the highest price.",
    },
    {
      tag: "Reasoning",
      type: "Best explanation",
      question:
        "An FRQ asks you to compare local, regional, and global effects of migration. Which course skill are you most clearly using?",
      answers: ["Data Analysis", "Source Analysis", "Scale Analysis", "Memorization"],
      correct: 2,
      explain:
        "Comparing effects across local, regional, and global levels is a scale-analysis move.",
    },
  ],
};

const MATCH_PAIRS = [
  { concept: "Site", example: "A city begins at a natural harbor with fresh water and defensible terrain." },
  { concept: "Situation", example: "A city grows because it lies near major trade routes and markets." },
  { concept: "Relocation diffusion", example: "Migrants bring a religion or language to a new region." },
  { concept: "Contagious diffusion", example: "A disease spreads rapidly through nearby contact." },
  { concept: "Unitary state", example: "Most power is concentrated in the central government." },
  { concept: "Federal state", example: "Power is shared between national and regional governments." },
  { concept: "Green Revolution", example: "Higher crop yields come from improved seeds, irrigation, and fertilizer." },
  { concept: "Von Thunen model", example: "Dairy and vegetables are located close to the urban market." },
  { concept: "Bid-rent theory", example: "Land values are highest near the CBD and decline outward." },
  { concept: "Gentrification", example: "Rising rents follow reinvestment in an older urban neighborhood." },
];

const BADGES = [
  { id: "starter", title: "Map Starter", detail: "Answer 5 total questions.", check: (stats) => stats.answered >= 5 },
  { id: "finder", title: "Pattern Finder", detail: "Answer 10 questions correctly.", check: (stats) => stats.correct >= 10 },
  { id: "streak", title: "Spatial Streak", detail: "Reach a streak of 5.", check: (stats) => stats.bestStreak >= 5 },
  { id: "clock", title: "Clock Runner", detail: "Score 6 or more in a timed sprint.", check: (stats) => stats.timedBest >= 6 },
  { id: "boss", title: "Boss Battle Clear", detail: "Complete one boss round.", check: (stats) => stats.bossWins >= 1 },
  { id: "connector", title: "Concept Connector", detail: "Complete one concept match round.", check: (stats) => stats.matchWins >= 1 },
];

const elements = {
  countdownValue: document.getElementById("countdownValue"),
  countdownLabel: document.getElementById("countdownLabel"),
  bigIdeaGrid: document.getElementById("bigIdeaGrid"),
  skillGrid: document.getElementById("skillGrid"),
  quizModeRow: document.getElementById("quizModeRow"),
  quizProgress: document.getElementById("quizProgress"),
  quizScore: document.getElementById("quizScore"),
  quizStreak: document.getElementById("quizStreak"),
  quizTag: document.getElementById("quizTag"),
  quizPromptType: document.getElementById("quizPromptType"),
  quizQuestion: document.getElementById("quizQuestion"),
  quizAnswers: document.getElementById("quizAnswers"),
  quizFeedback: document.getElementById("quizFeedback"),
  newQuestionBtn: document.getElementById("newQuestionBtn"),
  resetStatsBtn: document.getElementById("resetStatsBtn"),
  timedStatus: document.getElementById("timedStatus"),
  timedCountdown: document.getElementById("timedCountdown"),
  timedScore: document.getElementById("timedScore"),
  timedQuestion: document.getElementById("timedQuestion"),
  timedStartBtn: document.getElementById("timedStartBtn"),
  bossStatus: document.getElementById("bossStatus"),
  bossQuestion: document.getElementById("bossQuestion"),
  bossStartBtn: document.getElementById("bossStartBtn"),
  badgeGrid: document.getElementById("badgeGrid"),
  flashcardGrid: document.getElementById("flashcardGrid"),
  frqGrid: document.getElementById("frqGrid"),
  matchUnitGrid: document.getElementById("matchUnitGrid"),
  matchTopicGrid: document.getElementById("matchTopicGrid"),
  matchStatus: document.getElementById("matchStatus"),
  matchResetBtn: document.getElementById("matchResetBtn"),
  studyMix: document.getElementById("studyMix"),
  refreshMixBtn: document.getElementById("refreshMixBtn"),
  sourceList: document.getElementById("sourceList"),
};

let quizMode = "units";
let currentQuestion = null;
let stats = loadStats();
let timedRound = null;
let timedInterval = null;
let bossRound = null;
let matchState = null;

function init() {
  renderCountdown();
  renderBigIdeas();
  renderSkills();
  renderQuizModes();
  renderFlashcards();
  renderFrqs();
  renderBadges();
  renderStudyMix();
  renderSources();
  resetMatchRound();
  wireEvents();
  nextQuestion();
  updateScoreboard();
  renderTimedPanel();
  renderBossPanel();
  window.setInterval(renderCountdown, 60000);
}

function renderCountdown() {
  const now = new Date();
  const diff = EXAM_DATE.getTime() - now.getTime();

  if (diff <= 0) {
    elements.countdownValue.textContent = "It’s exam day";
    elements.countdownLabel.textContent = "Check your local start instructions";
    return;
  }

  const totalMinutes = Math.floor(diff / 60000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;

  elements.countdownValue.textContent = `${days}d ${hours}h ${minutes}m`;
  elements.countdownLabel.textContent = "until the May 5, 2026 exam";
}

function renderBigIdeas() {
  BIG_IDEAS.forEach((idea) => {
    const card = document.createElement("article");
    card.className = "mini-card";
    card.innerHTML = `<span class="chip">${idea.code}</span><strong>${idea.title}</strong><p>${idea.summary}</p>`;
    elements.bigIdeaGrid.append(card);
  });
}

function renderSkills() {
  SKILLS.forEach((skill) => {
    const card = document.createElement("article");
    card.className = "mini-card";
    card.innerHTML = `<span class="chip">Skill ${skill.code}</span><strong>${skill.title}</strong><p>${skill.summary}</p>`;
    elements.skillGrid.append(card);
  });
}

function renderQuizModes() {
  Object.keys(QUIZ_BANK).forEach((mode) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `mode-pill${mode === quizMode ? " active" : ""}`;
    button.textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
    button.addEventListener("click", () => {
      quizMode = mode;
      [...elements.quizModeRow.querySelectorAll(".mode-pill")].forEach((pill) => pill.classList.remove("active"));
      button.classList.add("active");
      nextQuestion();
    });
    elements.quizModeRow.append(button);
  });
}

function getRandomQuestion(mode) {
  const bank = QUIZ_BANK[mode];
  return bank[Math.floor(Math.random() * bank.length)];
}

function buildMixedQuestion() {
  const modes = Object.keys(QUIZ_BANK);
  return getRandomQuestion(modes[Math.floor(Math.random() * modes.length)]);
}

function nextQuestion() {
  currentQuestion = getRandomQuestion(quizMode);
  renderPracticeQuestion();
}

function renderPracticeQuestion() {
  elements.quizTag.textContent = currentQuestion.tag;
  elements.quizPromptType.textContent = currentQuestion.type;
  elements.quizQuestion.textContent = currentQuestion.question;
  elements.quizFeedback.classList.add("hidden");
  elements.quizFeedback.innerHTML = "";
  elements.quizAnswers.innerHTML = "";

  currentQuestion.answers.forEach((answer, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-btn";
    button.textContent = answer;
    button.addEventListener("click", () => gradePracticeAnswer(index, button));
    elements.quizAnswers.append(button);
  });
}

function gradePracticeAnswer(index, button) {
  [...elements.quizAnswers.querySelectorAll(".answer-btn")].forEach((entry, answerIndex) => {
    entry.disabled = true;
    if (answerIndex === currentQuestion.correct) {
      entry.classList.add("correct");
    }
  });

  const correct = index === currentQuestion.correct;
  if (!correct) {
    button.classList.add("incorrect");
  }

  updatePracticeStats(correct);
  elements.quizFeedback.classList.remove("hidden");
  elements.quizFeedback.innerHTML = `<strong>${correct ? "Correct" : "Not this one"}</strong><span>${currentQuestion.explain}</span>`;
}

function updatePracticeStats(correct) {
  stats.answered += 1;
  if (correct) {
    stats.correct += 1;
    stats.streak += 1;
    stats.bestStreak = Math.max(stats.bestStreak, stats.streak);
  } else {
    stats.streak = 0;
  }
  saveStats();
  updateScoreboard();
  renderBadges();
}

function updateScoreboard() {
  elements.quizProgress.textContent = `${stats.answered} answered`;
  elements.quizScore.textContent = `Score: ${stats.correct}`;
  elements.quizStreak.textContent = `Streak: ${stats.streak}`;
}

function renderTimedPanel() {
  if (!timedRound) {
    elements.timedStatus.textContent = "Ready for a 90-second mixed sprint built from real AP Human Geography concepts.";
    elements.timedCountdown.textContent = "01:30";
    elements.timedScore.textContent = `Best: ${stats.timedBest}`;
    elements.timedStartBtn.disabled = false;
    elements.timedStartBtn.textContent = "Start timed sprint";
    return;
  }

  elements.timedStatus.textContent = timedRound.active
    ? "Clock is live. Focus on applying concepts, models, and geographic reasoning."
    : `Timed sprint complete. You scored ${timedRound.score}.`;
  elements.timedCountdown.textContent = formatSeconds(timedRound.secondsLeft);
  elements.timedScore.textContent = `Round: ${timedRound.score} | Best: ${stats.timedBest}`;
  elements.timedStartBtn.disabled = timedRound.active;
  elements.timedStartBtn.textContent = timedRound.active ? "Sprint running" : "Start timed sprint";
}

function startTimedRound() {
  timedRound = {
    active: true,
    secondsLeft: 90,
    score: 0,
    question: buildMixedQuestion(),
  };

  renderTimedPanel();
  renderTimedQuestion();

  clearInterval(timedInterval);
  timedInterval = window.setInterval(() => {
    if (!timedRound) return;
    timedRound.secondsLeft -= 1;
    renderTimedPanel();
    if (timedRound.secondsLeft <= 0) {
      finishTimedRound();
    }
  }, 1000);
}

function renderTimedQuestion() {
  if (!timedRound) return;
  elements.timedQuestion.innerHTML = `<div class="game-question-head"><span class="chip">${timedRound.question.tag}</span><strong>${timedRound.question.question}</strong></div>`;
  const answers = document.createElement("div");
  answers.className = "answer-grid compact-grid";
  timedRound.question.answers.forEach((answer, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-btn";
    button.textContent = answer;
    button.addEventListener("click", () => gradeTimedAnswer(index));
    answers.append(button);
  });
  elements.timedQuestion.append(answers);
}

function gradeTimedAnswer(index) {
  if (!timedRound || !timedRound.active) return;
  if (index === timedRound.question.correct) {
    timedRound.score += 1;
  }
  timedRound.question = buildMixedQuestion();
  renderTimedPanel();
  renderTimedQuestion();
}

function finishTimedRound() {
  clearInterval(timedInterval);
  timedRound.active = false;
  stats.timedBest = Math.max(stats.timedBest, timedRound.score);
  saveStats();
  renderBadges();
  renderTimedPanel();
  elements.timedQuestion.innerHTML = `<div class="game-summary"><strong>Timed sprint complete</strong><p>You finished with ${timedRound.score} correct in 90 seconds.</p></div>`;
}

function startBossRound() {
  bossRound = {
    questions: [...QUIZ_BANK.units, ...QUIZ_BANK.exam, ...QUIZ_BANK.skills].sort(() => Math.random() - 0.5).slice(0, 7),
    index: 0,
    correct: 0,
    total: 7,
    finished: false,
  };
  renderBossPanel();
  renderBossQuestion();
}

function renderBossPanel() {
  if (!bossRound) {
    elements.bossStatus.textContent = "Seven applied questions. Go for the clean clear.";
    return;
  }
  if (bossRound.finished) {
    elements.bossStatus.textContent = `Boss round complete: ${bossRound.correct}/${bossRound.total}.`;
    return;
  }
  elements.bossStatus.textContent = `Boss round: ${bossRound.index + 1}/${bossRound.total}`;
}

function renderBossQuestion() {
  if (!bossRound) return;
  if (bossRound.finished) {
    elements.bossQuestion.innerHTML = `<div class="game-summary"><strong>Boss battle complete</strong><p>You got ${bossRound.correct} of ${bossRound.total} mixed questions right.</p></div>`;
    return;
  }

  const question = bossRound.questions[bossRound.index];
  elements.bossQuestion.innerHTML = `<div class="game-question-head"><span class="chip">${question.tag}</span><strong>${question.question}</strong><p class="muted">${question.type}</p></div>`;
  const answers = document.createElement("div");
  answers.className = "answer-grid compact-grid";
  question.answers.forEach((answer, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-btn";
    button.textContent = answer;
    button.addEventListener("click", () => gradeBossAnswer(index));
    answers.append(button);
  });
  elements.bossQuestion.append(answers);
}

function gradeBossAnswer(index) {
  const question = bossRound.questions[bossRound.index];
  if (index === question.correct) {
    bossRound.correct += 1;
  }
  bossRound.index += 1;
  if (bossRound.index >= bossRound.total) {
    bossRound.finished = true;
    stats.bossWins += 1;
    saveStats();
    renderBadges();
  }
  renderBossPanel();
  renderBossQuestion();
}

function renderBadges() {
  elements.badgeGrid.innerHTML = "";
  BADGES.forEach((badge) => {
    const unlocked = badge.check(stats);
    const card = document.createElement("article");
    card.className = `badge-card${unlocked ? " unlocked" : ""}`;
    card.innerHTML = `<span class="chip">${unlocked ? "Unlocked" : "Locked"}</span><strong>${badge.title}</strong><p>${badge.detail}</p>`;
    elements.badgeGrid.append(card);
  });
}

function renderFlashcards() {
  FLASHCARDS.forEach((cardData) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "flashcard";
    button.setAttribute("aria-label", `Flip flashcard for ${cardData.front}`);
    button.innerHTML = `
      <div class="flashcard-inner">
        <div class="flashcard-face flashcard-front">
          <span class="chip">Tap to flip</span>
          <strong>${cardData.front}</strong>
          <span class="muted">Say the answer out loud before you turn it.</span>
        </div>
        <div class="flashcard-face flashcard-back">
          <span class="chip">Answer</span>
          <strong>${cardData.front}</strong>
          <span>${cardData.back}</span>
        </div>
      </div>
    `;
    button.addEventListener("click", () => button.classList.toggle("flipped"));
    elements.flashcardGrid.append(button);
  });
}

function renderFrqs() {
  FRQ_CARDS.forEach((cardData) => {
    const card = document.createElement("article");
    card.className = "frq-card";
    card.innerHTML = `<span class="chip">${cardData.chip}</span><strong>${cardData.title}</strong><ul>${cardData.notes
      .map((note) => `<li>${note}</li>`)
      .join("")}</ul>`;
    elements.frqGrid.append(card);
  });
}

function resetMatchRound() {
  matchState = {
    selectedConcept: null,
    remaining: [...MATCH_PAIRS].sort(() => Math.random() - 0.5).slice(0, 6),
  };
  elements.matchStatus.textContent = "Pick a concept, then match the real-world example to it.";
  renderMatchGame();
}

function renderMatchGame() {
  elements.matchUnitGrid.innerHTML = "";
  elements.matchTopicGrid.innerHTML = "";

  const concepts = [...new Set(matchState.remaining.map((pair) => pair.concept))].sort();

  concepts.forEach((concept) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `mode-pill match-pill${matchState.selectedConcept === concept ? " active" : ""}`;
    button.textContent = concept;
    button.addEventListener("click", () => {
      matchState.selectedConcept = concept;
      renderMatchGame();
    });
    elements.matchUnitGrid.append(button);
  });

  matchState.remaining.forEach((pair) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-btn";
    button.textContent = pair.example;
    button.addEventListener("click", () => handleMatch(pair));
    elements.matchTopicGrid.append(button);
  });
}

function handleMatch(pair) {
  if (!matchState.selectedConcept) {
    elements.matchStatus.textContent = "Choose a concept first.";
    return;
  }

  if (pair.concept === matchState.selectedConcept) {
    matchState.remaining = matchState.remaining.filter((entry) => entry.example !== pair.example);
    elements.matchStatus.textContent = `Correct: that example fits ${pair.concept}.`;
  } else {
    elements.matchStatus.textContent = `Not quite. That example does not fit ${matchState.selectedConcept}.`;
  }

  if (matchState.remaining.length === 0) {
    stats.matchWins += 1;
    saveStats();
    renderBadges();
    elements.matchStatus.textContent = "Match round cleared. Every concept landed on the right example.";
  }

  renderMatchGame();
}

function renderStudyMix() {
  elements.studyMix.innerHTML = "";
  const randomModes = Object.keys(QUIZ_BANK).sort(() => Math.random() - 0.5).slice(0, 3);
  const randomPair = MATCH_PAIRS[Math.floor(Math.random() * MATCH_PAIRS.length)];
  const steps = [
    `Start with a ${randomModes[0]} round and say why each correct answer fits the scenario, not just what it is called.`,
    `Do one timed sprint and watch for repeated concepts like diffusion, urbanization, migration, or development.`,
    `Write one quick FRQ-style explanation that connects a real-world example to a model such as the demographic transition model, bid-rent theory, or von Thunen.`,
    `Finish with a concept match round and explain why "${randomPair.example}" fits ${randomPair.concept}.`,
  ];

  steps.forEach((detail, index) => {
    const item = document.createElement("li");
    item.className = "study-step";
    item.innerHTML = `<strong>Step ${index + 1}</strong><span>${detail}</span>`;
    elements.studyMix.append(item);
  });
}

function renderSources() {
  SOURCES.forEach((source) => {
    const item = document.createElement("li");
    item.innerHTML = `<a href="${source.url}" target="_blank" rel="noreferrer">${source.label}</a><br />${source.note}`;
    elements.sourceList.append(item);
  });
}

function wireEvents() {
  elements.newQuestionBtn.addEventListener("click", nextQuestion);
  elements.resetStatsBtn.addEventListener("click", () => {
    stats = defaultStats();
    saveStats();
    renderBadges();
    updateScoreboard();
    timedRound = null;
    bossRound = null;
    renderTimedPanel();
    renderBossPanel();
    nextQuestion();
  });
  elements.timedStartBtn.addEventListener("click", startTimedRound);
  elements.bossStartBtn.addEventListener("click", startBossRound);
  elements.matchResetBtn.addEventListener("click", resetMatchRound);
  elements.refreshMixBtn.addEventListener("click", renderStudyMix);
}

function defaultStats() {
  return {
    answered: 0,
    correct: 0,
    streak: 0,
    bestStreak: 0,
    timedBest: 0,
    bossWins: 0,
    matchWins: 0,
  };
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultStats();
    const parsed = JSON.parse(raw);
    return {
      answered: Number(parsed.answered) || 0,
      correct: Number(parsed.correct) || 0,
      streak: Number(parsed.streak) || 0,
      bestStreak: Number(parsed.bestStreak) || 0,
      timedBest: Number(parsed.timedBest) || 0,
      bossWins: Number(parsed.bossWins) || 0,
      matchWins: Number(parsed.matchWins) || 0,
    };
  } catch (error) {
    return defaultStats();
  }
}

function saveStats() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
}

function formatSeconds(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

init();
