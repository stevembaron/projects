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

const EXAM_SECTIONS = [
  {
    title: "Section I: Multiple Choice",
    chip: "60 questions | 1 hour | 50%",
    points: [
      "Includes both individual questions and set-based questions.",
      "Can ask students to analyze concepts, processes, patterns, and relationships.",
      "Can use maps, tables, charts, graphs, satellite images, and infographics as evidence.",
    ],
  },
  {
    title: "Section II: Free Response",
    chip: "3 questions | 1 hour 15 minutes | 50%",
    points: [
      "Question 1 has no stimulus.",
      "Question 2 uses one stimulus such as data, an image, or a map.",
      "Question 3 uses two stimuli, and at least one FRQ assesses analysis across geographic scales.",
    ],
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
  {
    front: "Unit 1",
    back: "Thinking Geographically is the smallest unit by exam weight and centers on maps, data, scale, and regions.",
  },
  {
    front: "Unit 2",
    back: "Population and Migration asks you to work with density, demographic change, policies, and migration effects.",
  },
  {
    front: "Unit 3",
    back: "Culture questions often connect diffusion, cultural landscapes, religion, language, colonialism, and globalization.",
  },
  {
    front: "Unit 4",
    back: "Political geography includes states, nations, borders, governance, sovereignty, and devolutionary pressures.",
  },
  {
    front: "Unit 5",
    back: "Agriculture and rural land use include origins of farming, diffusion, production regions, and the Green Revolution.",
  },
  {
    front: "Unit 6",
    back: "Cities and urban land use focus on urbanization, internal city structure, infrastructure, and sustainability.",
  },
  {
    front: "Unit 7",
    back: "Industrial and economic development covers industrialization, economic sectors, development theories, and trade.",
  },
  {
    front: "MCQ",
    back: "Section I has 60 multiple-choice questions, lasts 1 hour, and is worth 50% of the exam.",
  },
  {
    front: "FRQ",
    back: "Section II has 3 free-response questions, lasts 1 hour 15 minutes, and is worth 50% of the exam.",
  },
  {
    front: "Digital format",
    back: "The 2026 AP Human Geography exam is fully digital in the Bluebook app.",
  },
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
  units: [
    {
      tag: "Units",
      type: "Match the unit",
      question: "Which unit includes the Green Revolution?",
      answers: [
        "Unit 3: Cultural Patterns and Processes",
        "Unit 5: Agriculture and Rural Land-Use Patterns and Processes",
        "Unit 6: Cities and Urban Land-Use Patterns and Processes",
        "Unit 7: Industrial and Economic Development Patterns and Processes",
      ],
      correct: 1,
      explain: "The Green Revolution is listed in Unit 5 on the official AP Human Geography course page.",
    },
    {
      tag: "Units",
      type: "Match the unit",
      question: "Which unit focuses on maps, geospatial data, scale, and regions?",
      answers: [
        "Unit 1: Thinking Geographically",
        "Unit 2: Population and Migration Patterns and Processes",
        "Unit 4: Political Patterns and Processes",
        "Unit 6: Cities and Urban Land-Use Patterns and Processes",
      ],
      correct: 0,
      explain: "Unit 1 is the introductory tools-and-methods unit.",
    },
    {
      tag: "Units",
      type: "Match the unit",
      question: "A question about unitary versus federal states belongs most directly to which unit?",
      answers: ["Unit 2", "Unit 3", "Unit 4", "Unit 7"],
      correct: 2,
      explain: "Forms of government such as unitary and federal states are part of Unit 4.",
    },
    {
      tag: "Units",
      type: "Match the unit",
      question: "Which unit studies city infrastructure and urban design initiatives?",
      answers: ["Unit 3", "Unit 4", "Unit 5", "Unit 6"],
      correct: 3,
      explain: "Those topics are listed under Unit 6 on the official course page.",
    },
    {
      tag: "Units",
      type: "Match the unit",
      question: "Which unit covers economic sectors and trade in the world economy?",
      answers: ["Unit 1", "Unit 5", "Unit 7", "None of these"],
      correct: 2,
      explain: "Those are official Unit 7 topics.",
    },
    {
      tag: "Units",
      type: "Weighting check",
      question: "Which unit has the smallest multiple-choice weighting range?",
      answers: ["Unit 1", "Unit 2", "Unit 5", "Unit 7"],
      correct: 0,
      explain: "Unit 1 is weighted 8%–10%; Units 2–7 are each 12%–17%.",
    },
  ],
  exam: [
    {
      tag: "Exam",
      type: "Structure check",
      question: "How many multiple-choice questions are on the AP Human Geography exam?",
      answers: ["50", "60", "70", "80"],
      correct: 1,
      explain: "Section I has 60 multiple-choice questions.",
    },
    {
      tag: "Exam",
      type: "Structure check",
      question: "How long is the full AP Human Geography exam?",
      answers: ["2 hours", "2 hours 15 minutes", "2 hours 30 minutes", "3 hours"],
      correct: 1,
      explain: "The official assessment page lists 2 hours 15 minutes total.",
    },
    {
      tag: "Exam",
      type: "FRQ setup",
      question: "Which free-response question includes two stimuli?",
      answers: ["Question 1", "Question 2", "Question 3", "All three"],
      correct: 2,
      explain: "Question 3 includes two stimuli.",
    },
    {
      tag: "Exam",
      type: "FRQ setup",
      question: "Which free-response question has no stimulus?",
      answers: ["Question 1", "Question 2", "Question 3", "None of them"],
      correct: 0,
      explain: "Question 1 is the no-stimulus FRQ.",
    },
    {
      tag: "Exam",
      type: "Format",
      question: "What is true about the 2026 AP Human Geography exam format?",
      answers: [
        "It is paper-only",
        "It is oral only",
        "It is fully digital in Bluebook",
        "Only the FRQs are digital",
      ],
      correct: 2,
      explain: "The official AP Students assessment page says the exam is fully digital in Bluebook.",
    },
    {
      tag: "Exam",
      type: "Timing",
      question: "How much of the score comes from the free-response section?",
      answers: ["25%", "40%", "50%", "60%"],
      correct: 2,
      explain: "Section II is worth 50% of the exam score.",
    },
  ],
  skills: [
    {
      tag: "Skills",
      type: "Pick the skill",
      question: "A prompt asks you to analyze a table and graph showing migration data. Which skill category is most direct?",
      answers: [
        "Concepts and Processes",
        "Spatial Relationships",
        "Data Analysis",
        "Scale Analysis",
      ],
      correct: 2,
      explain: "Skill Category 3 is about quantitative geographic data in tables, charts, graphs, maps, and infographics.",
    },
    {
      tag: "Skills",
      type: "Pick the skill",
      question: "A prompt asks you to explain how a pattern changes from the local scale to the global scale. Which skill category fits best?",
      answers: [
        "Source Analysis",
        "Scale Analysis",
        "Concepts and Processes",
        "Data Analysis",
      ],
      correct: 1,
      explain: "Skill Category 5 focuses on using geographic scales to explain spatial relationships.",
    },
    {
      tag: "Skills",
      type: "Pick the skill",
      question: "A prompt asks you to compare patterns shown in two maps and draw conclusions. Which skill category fits best?",
      answers: [
        "Spatial Relationships",
        "Source Analysis",
        "Concepts and Processes",
        "Scale Analysis",
      ],
      correct: 1,
      explain: "Comparing patterns across visual sources is a Source Analysis move.",
    },
    {
      tag: "Skills",
      type: "Pick the skill",
      question: "A prompt asks you to explain a geographic model and compare it to another theory. Which skill category is most direct?",
      answers: [
        "Concepts and Processes",
        "Source Analysis",
        "Data Analysis",
        "Scale Analysis",
      ],
      correct: 0,
      explain: "Skill Category 1 centers on explaining and comparing concepts, processes, models, and theories.",
    },
    {
      tag: "Skills",
      type: "Pick the skill",
      question: "A prompt asks you to explain why a spatial pattern appears in one region and not another. Which skill category is closest?",
      answers: [
        "Spatial Relationships",
        "Data Analysis",
        "Source Analysis",
        "Concepts and Processes",
      ],
      correct: 0,
      explain: "Skill Category 2 focuses on spatial patterns, networks, relationships, and outcomes in applied contexts.",
    },
  ],
};

const MATCH_PAIRS = UNITS.flatMap((unit) =>
  unit.officialTopics.slice(0, 2).map((topic) => ({
    unitId: unit.id,
    unitShort: unit.short,
    topic,
  })),
);

const BADGES = [
  { id: "starter", title: "Map Starter", detail: "Answer 5 total questions.", check: (stats) => stats.answered >= 5 },
  { id: "finder", title: "Pattern Finder", detail: "Answer 10 questions correctly.", check: (stats) => stats.correct >= 10 },
  { id: "streak", title: "Spatial Streak", detail: "Reach a streak of 5.", check: (stats) => stats.bestStreak >= 5 },
  { id: "clock", title: "Clock Runner", detail: "Score 6 or more in a timed sprint.", check: (stats) => stats.timedBest >= 6 },
  { id: "boss", title: "Boss Battle Clear", detail: "Complete one boss round.", check: (stats) => stats.bossWins >= 1 },
  { id: "cartographer", title: "Topic Cartographer", detail: "Complete one topic match round.", check: (stats) => stats.matchWins >= 1 },
];

const elements = {
  countdownValue: document.getElementById("countdownValue"),
  countdownLabel: document.getElementById("countdownLabel"),
  bigIdeaGrid: document.getElementById("bigIdeaGrid"),
  skillGrid: document.getElementById("skillGrid"),
  examSectionGrid: document.getElementById("examSectionGrid"),
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
  unitGrid: document.getElementById("unitGrid"),
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
  renderExamSections();
  renderQuizModes();
  renderUnits();
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

function renderExamSections() {
  EXAM_SECTIONS.forEach((section) => {
    const card = document.createElement("article");
    card.className = "section-card";
    card.innerHTML = `<span class="chip">${section.chip}</span><strong>${section.title}</strong><ul>${section.points
      .map((point) => `<li>${point}</li>`)
      .join("")}</ul>`;
    elements.examSectionGrid.append(card);
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
    elements.timedStatus.textContent = "Ready for a 90-second mixed sprint.";
    elements.timedCountdown.textContent = "01:30";
    elements.timedScore.textContent = `Best: ${stats.timedBest}`;
    elements.timedStartBtn.disabled = false;
    elements.timedStartBtn.textContent = "Start timed sprint";
    return;
  }

  elements.timedStatus.textContent = timedRound.active
    ? "Clock is live. Questions are pulled from units, exam structure, and skills."
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
    elements.bossStatus.textContent = "Seven mixed questions. Go for the clean clear.";
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

function renderUnits() {
  UNITS.forEach((unit) => {
    const card = document.createElement("article");
    card.className = "unit-card";
    card.innerHTML = `
      <header>
        <div class="pill-row">
          <span class="chip">${unit.short}</span>
          <span class="chip">${unit.weight} MCQ</span>
        </div>
        <h3>${unit.title}</h3>
        <p>${unit.summary}</p>
      </header>
      <strong>Course page summary</strong>
      <ul>${unit.topics.map((topic) => `<li>${topic}</li>`).join("")}</ul>
      <strong>Official topic names</strong>
      <ul>${unit.officialTopics.map((topic) => `<li>${topic}</li>`).join("")}</ul>
    `;
    elements.unitGrid.append(card);
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
    selectedUnitId: null,
    remaining: [...MATCH_PAIRS].sort(() => Math.random() - 0.5).slice(0, 6),
  };
  elements.matchStatus.textContent = "Pick a unit, then match the official topic name to it.";
  renderMatchGame();
}

function renderMatchGame() {
  elements.matchUnitGrid.innerHTML = "";
  elements.matchTopicGrid.innerHTML = "";

  UNITS.forEach((unit) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `mode-pill match-pill${matchState.selectedUnitId === unit.id ? " active" : ""}`;
    button.textContent = unit.short;
    button.addEventListener("click", () => {
      matchState.selectedUnitId = unit.id;
      renderMatchGame();
    });
    elements.matchUnitGrid.append(button);
  });

  matchState.remaining.forEach((pair) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-btn";
    button.textContent = pair.topic;
    button.addEventListener("click", () => handleMatch(pair));
    elements.matchTopicGrid.append(button);
  });
}

function handleMatch(pair) {
  if (!matchState.selectedUnitId) {
    elements.matchStatus.textContent = "Choose a unit first.";
    return;
  }

  if (pair.unitId === matchState.selectedUnitId) {
    matchState.remaining = matchState.remaining.filter((entry) => entry.topic !== pair.topic);
    elements.matchStatus.textContent = `Correct: ${pair.topic} belongs to ${pair.unitShort}.`;
  } else {
    const wrongUnit = UNITS.find((unit) => unit.id === matchState.selectedUnitId);
    elements.matchStatus.textContent = `Not quite. ${pair.topic} does not belong to ${wrongUnit.short}.`;
  }

  if (matchState.remaining.length === 0) {
    stats.matchWins += 1;
    saveStats();
    renderBadges();
    elements.matchStatus.textContent = "Match round cleared. Every topic landed on the right unit.";
  }

  renderMatchGame();
}

function renderStudyMix() {
  elements.studyMix.innerHTML = "";
  const selectedUnits = [...UNITS].sort(() => Math.random() - 0.5).slice(0, 3);
  const randomSkill = SKILLS[Math.floor(Math.random() * SKILLS.length)];
  const steps = [
    `Spend 12 minutes on ${selectedUnits[0].title}, then say two official topics without looking.`,
    `Run a sprint round and explain why the correct answers fit ${randomSkill.title}.`,
    `Write one FRQ-style paragraph connecting ${selectedUnits[1].title} to one big idea.`,
    `Close by naming the weight range and one official topic from ${selectedUnits[2].short}.`,
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
