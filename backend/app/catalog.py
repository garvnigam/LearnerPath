"""Curated free-course catalog from top providers worldwide.
MIT OpenCourseWare is also fetched live via MIT Learn API in mit_learn.py.
This module is a hand-picked static list of stable, freely accessible, world-class
courses and YouTube playlists — the LLM is allowed to add other top-class
courses/playlists on top of this when a subject is thinly represented here."""

CURATED: list[dict] = [
    # ------------------------------------------------------------------
    # Stanford
    # ------------------------------------------------------------------
    {
        "title": "CS229: Machine Learning",
        "provider": "Stanford",
        "url": "https://cs229.stanford.edu/",
        "level": "advanced",
        "description": "Andrew Ng's classic graduate ML course covering supervised learning, kernels, SVMs, deep learning, and reinforcement learning.",
        "duration": "10 weeks",
        "topics": ["machine learning", "computer science", "ai"],
        "format": "course",
    },
    {
        "title": "CS229: Machine Learning (Full Lectures)",
        "provider": "Stanford (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU",
        "level": "advanced",
        "description": "Full Stanford CS229 lecture playlist on YouTube.",
        "duration": "~30 hours",
        "topics": ["machine learning", "computer science", "ai"],
        "format": "playlist",
    },
    {
        "title": "CS230: Deep Learning",
        "provider": "Stanford",
        "url": "https://cs230.stanford.edu/",
        "level": "advanced",
        "description": "Deep learning foundations: CNNs, RNNs, LSTMs, Transformers.",
        "duration": "10 weeks",
        "topics": ["deep learning", "cnn", "rnn", "computer science"],
        "format": "course",
    },
    {
        "title": "CS231n: Convolutional Neural Networks for Visual Recognition",
        "provider": "Stanford",
        "url": "https://cs231n.stanford.edu/",
        "level": "advanced",
        "description": "Definitive course on CNNs for computer vision.",
        "duration": "10 weeks",
        "topics": ["cnn", "computer vision", "deep learning"],
        "format": "course",
    },
    {
        "title": "CS224n: NLP with Deep Learning (Full Lectures)",
        "provider": "Stanford (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLoROMvodv4rOSH4v6133s9LFPRHjEmbmJ",
        "level": "advanced",
        "description": "NLP with word vectors, RNNs, attention and Transformers — full YouTube lectures.",
        "duration": "~25 hours",
        "topics": ["nlp", "rnn", "transformer", "deep learning"],
        "format": "playlist",
    },
    {
        "title": "CS106A: Programming Methodology",
        "provider": "Stanford",
        "url": "https://web.stanford.edu/class/cs106a/",
        "level": "beginner",
        "description": "Intro to programming in Python. No experience required.",
        "duration": "10 weeks",
        "topics": ["programming", "python", "computer science"],
        "format": "course",
    },
    {
        "title": "Statistical Learning (Hastie & Tibshirani)",
        "provider": "Stanford Online",
        "url": "https://online.stanford.edu/courses/sohs-ystatslearning-statistical-learning",
        "level": "intermediate",
        "description": "Classic Statistical Learning course based on ISLR/ESL.",
        "duration": "10 weeks",
        "topics": ["statistics", "machine learning", "mathematics"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # MIT (OCW YouTube — top playlists in addition to MIT Learn API results)
    # ------------------------------------------------------------------
    {
        "title": "MIT 6.006: Introduction to Algorithms",
        "provider": "MIT OCW (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLUl4u3cNGP63EdVPNLG3ToM6LaEUuStEY",
        "level": "intermediate",
        "description": "Erik Demaine's full MIT 6.006 lectures on algorithms and data structures.",
        "duration": "~25 hours",
        "topics": ["algorithms", "data structures", "computer science"],
        "format": "playlist",
    },
    {
        "title": "MIT 6.034: Artificial Intelligence (Patrick Winston)",
        "provider": "MIT OCW (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLUl4u3cNGP63gFHB6xb-kVBiQHYe_4hSi",
        "level": "intermediate",
        "description": "Legendary Patrick Winston AI lectures.",
        "duration": "~25 hours",
        "topics": ["ai", "computer science"],
        "format": "playlist",
    },
    {
        "title": "MIT 18.06: Linear Algebra (Gilbert Strang)",
        "provider": "MIT OCW (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLE7DDD91010BC51F8",
        "level": "beginner",
        "description": "Gilbert Strang's iconic linear algebra course.",
        "duration": "~30 hours",
        "topics": ["linear algebra", "mathematics"],
        "format": "playlist",
    },
    {
        "title": "MIT 18.01: Single Variable Calculus",
        "provider": "MIT OCW",
        "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/",
        "level": "beginner",
        "description": "Full lectures + problem sets for single-variable calculus.",
        "duration": "self-paced",
        "topics": ["calculus", "mathematics"],
        "format": "course",
    },
    {
        "title": "MIT 8.01: Physics I - Classical Mechanics (Walter Lewin)",
        "provider": "MIT OCW (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLyQSN7X0ro203puVhQsmCj9qhlFQ-As8e",
        "level": "beginner",
        "description": "Walter Lewin's celebrated introductory physics lectures.",
        "duration": "~35 hours",
        "topics": ["physics", "science"],
        "format": "playlist",
    },

    # ------------------------------------------------------------------
    # Harvard
    # ------------------------------------------------------------------
    {
        "title": "CS50: Introduction to Computer Science",
        "provider": "Harvard (edX)",
        "url": "https://cs50.harvard.edu/x/",
        "level": "beginner",
        "description": "Harvard's flagship intro to CS: C, Python, SQL, web.",
        "duration": "12 weeks",
        "topics": ["computer science", "programming", "algorithms"],
        "format": "course",
    },
    {
        "title": "CS50AI: Introduction to AI with Python",
        "provider": "Harvard (edX)",
        "url": "https://cs50.harvard.edu/ai/",
        "level": "intermediate",
        "description": "Search, knowledge, uncertainty, optimization, learning, neural networks.",
        "duration": "7 weeks",
        "topics": ["ai", "machine learning", "python"],
        "format": "course",
    },
    {
        "title": "CS50 Business (Understanding Technology)",
        "provider": "Harvard (edX)",
        "url": "https://cs50.harvard.edu/business/",
        "level": "beginner",
        "description": "CS50 for business students and managers.",
        "duration": "6 weeks",
        "topics": ["business", "computer science"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # IIT / NPTEL
    # ------------------------------------------------------------------
    {
        "title": "Introduction to Machine Learning (IIT Madras)",
        "provider": "NPTEL / IIT Madras",
        "url": "https://nptel.ac.in/courses/106106139",
        "level": "intermediate",
        "description": "Balaraman Ravindran's ML course from IIT Madras.",
        "duration": "12 weeks",
        "topics": ["machine learning", "computer science"],
        "format": "course",
    },
    {
        "title": "Deep Learning (IIT Kharagpur)",
        "provider": "NPTEL / IIT Kharagpur",
        "url": "https://nptel.ac.in/courses/106105215",
        "level": "advanced",
        "description": "Comprehensive deep learning from IIT Kharagpur.",
        "duration": "12 weeks",
        "topics": ["deep learning", "cnn", "rnn"],
        "format": "course",
    },
    {
        "title": "Data Structures and Algorithms (IIT Delhi)",
        "provider": "NPTEL / IIT Delhi",
        "url": "https://nptel.ac.in/courses/106102064",
        "level": "intermediate",
        "description": "Core DS&A from IIT Delhi.",
        "duration": "12 weeks",
        "topics": ["algorithms", "data structures", "computer science"],
        "format": "course",
    },
    {
        "title": "Programming, DS & Algorithms using Python (IIT Madras)",
        "provider": "NPTEL / IIT Madras",
        "url": "https://nptel.ac.in/courses/106106145",
        "level": "beginner",
        "description": "Python + DS&A fundamentals.",
        "duration": "8 weeks",
        "topics": ["python", "programming", "algorithms"],
        "format": "course",
    },
    {
        "title": "Financial Accounting (IIM Bangalore / NPTEL)",
        "provider": "NPTEL",
        "url": "https://nptel.ac.in/courses/110104068",
        "level": "beginner",
        "description": "Foundations of financial accounting.",
        "duration": "12 weeks",
        "topics": ["accounting", "finance", "business", "chartered accountancy"],
        "format": "course",
    },
    {
        "title": "Business Statistics (IIT Roorkee / NPTEL)",
        "provider": "NPTEL / IIT Roorkee",
        "url": "https://nptel.ac.in/courses/110107114",
        "level": "beginner",
        "description": "Statistics for business decisions.",
        "duration": "12 weeks",
        "topics": ["statistics", "business", "mathematics"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # Princeton
    # ------------------------------------------------------------------
    {
        "title": "Algorithms, Part I",
        "provider": "Princeton (Coursera)",
        "url": "https://www.coursera.org/learn/algorithms-part1",
        "level": "intermediate",
        "description": "Sedgewick & Wayne's classic algorithms course.",
        "duration": "6 weeks",
        "topics": ["algorithms", "data structures", "computer science"],
        "format": "course",
    },
    {
        "title": "Algorithms, Part II",
        "provider": "Princeton (Coursera)",
        "url": "https://www.coursera.org/learn/algorithms-part2",
        "level": "advanced",
        "description": "Graph, string, and advanced algorithms.",
        "duration": "6 weeks",
        "topics": ["algorithms", "data structures", "computer science"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # Yale / Oxford / Cambridge / others (top-class free lectures)
    # ------------------------------------------------------------------
    {
        "title": "Financial Markets (Robert Shiller)",
        "provider": "Yale (Coursera)",
        "url": "https://www.coursera.org/learn/financial-markets-global",
        "level": "beginner",
        "description": "Nobel laureate Robert Shiller's course on financial markets.",
        "duration": "7 weeks",
        "topics": ["finance", "business", "economics"],
        "format": "course",
    },
    {
        "title": "Game Theory",
        "provider": "Stanford & UBC (Coursera)",
        "url": "https://www.coursera.org/learn/game-theory-1",
        "level": "intermediate",
        "description": "Rigorous intro to game theory.",
        "duration": "8 weeks",
        "topics": ["economics", "mathematics", "business"],
        "format": "course",
    },
    {
        "title": "Justice with Michael Sandel",
        "provider": "Harvard (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PL30C13C91CFFEFEA6",
        "level": "beginner",
        "description": "Michael Sandel's world-famous course on moral & political philosophy.",
        "duration": "~12 hours",
        "topics": ["philosophy", "humanities"],
        "format": "playlist",
    },

    # ------------------------------------------------------------------
    # YouTube — top-class independent creators
    # ------------------------------------------------------------------
    {
        "title": "Essence of Linear Algebra",
        "provider": "3Blue1Brown (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
        "level": "beginner",
        "description": "Visual intuition for linear algebra.",
        "duration": "~3 hours",
        "topics": ["linear algebra", "mathematics"],
        "format": "playlist",
    },
    {
        "title": "Essence of Calculus",
        "provider": "3Blue1Brown (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr",
        "level": "beginner",
        "description": "Visual intuition for calculus.",
        "duration": "~4 hours",
        "topics": ["calculus", "mathematics"],
        "format": "playlist",
    },
    {
        "title": "Neural Networks (3Blue1Brown)",
        "provider": "3Blue1Brown (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
        "level": "beginner",
        "description": "Visual, intuitive intro to neural networks & backprop.",
        "duration": "~2 hours",
        "topics": ["deep learning", "machine learning", "mathematics"],
        "format": "playlist",
    },
    {
        "title": "Neural Networks: Zero to Hero (Andrej Karpathy)",
        "provider": "Andrej Karpathy (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ",
        "level": "advanced",
        "description": "Build GPT-style models from scratch, step by step.",
        "duration": "~15 hours",
        "topics": ["deep learning", "transformer", "nlp", "ai"],
        "format": "playlist",
    },
    {
        "title": "Practical Deep Learning for Coders",
        "provider": "fast.ai",
        "url": "https://course.fast.ai/",
        "level": "intermediate",
        "description": "Top-down practical DL course used worldwide.",
        "duration": "~40 hours",
        "topics": ["deep learning", "machine learning", "ai"],
        "format": "course",
    },
    {
        "title": "StatQuest with Josh Starmer",
        "provider": "StatQuest (YouTube)",
        "url": "https://www.youtube.com/@statquest/playlists",
        "level": "beginner",
        "description": "Clearly-explained statistics, ML and data science.",
        "duration": "playlists",
        "topics": ["statistics", "machine learning", "mathematics"],
        "format": "playlist",
    },
    {
        "title": "freeCodeCamp — Full-Stack Web Development",
        "provider": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/learn",
        "level": "beginner",
        "description": "Interactive full-stack curriculum (HTML/CSS/JS/React/Node).",
        "duration": "self-paced",
        "topics": ["web development", "javascript", "programming"],
        "format": "course",
    },
    {
        "title": "The Missing Semester of Your CS Education",
        "provider": "MIT (YouTube)",
        "url": "https://missing.csail.mit.edu/",
        "level": "beginner",
        "description": "Shell, git, editors, tooling every CS student should know.",
        "duration": "~10 hours",
        "topics": ["computer science", "programming", "tools"],
        "format": "course",
    },
    {
        "title": "Khan Academy — Math (K-12 → early college)",
        "provider": "Khan Academy",
        "url": "https://www.khanacademy.org/math",
        "level": "beginner",
        "description": "World-class free math curriculum from arithmetic to multivariable calculus.",
        "duration": "self-paced",
        "topics": ["mathematics", "calculus", "algebra", "statistics"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------
    {
        "title": "The Feynman Lectures on Physics",
        "provider": "Caltech",
        "url": "https://www.feynmanlectures.caltech.edu/",
        "level": "intermediate",
        "description": "Complete free online edition of Feynman's classic physics lectures.",
        "duration": "self-paced",
        "topics": ["physics", "science"],
        "format": "course",
    },
    {
        "title": "Susskind's Theoretical Minimum",
        "provider": "Stanford (YouTube)",
        "url": "https://www.youtube.com/@stanford/playlists?query=theoretical+minimum",
        "level": "advanced",
        "description": "Leonard Susskind's celebrated theoretical physics lectures.",
        "duration": "playlists",
        "topics": ["physics", "science"],
        "format": "playlist",
    },

    # ------------------------------------------------------------------
    # Music / Arts / Humanities
    # ------------------------------------------------------------------
    {
        "title": "Fundamentals of Music Theory",
        "provider": "University of Edinburgh (Coursera)",
        "url": "https://www.coursera.org/learn/edinburgh-music-theory",
        "level": "beginner",
        "description": "Music theory fundamentals.",
        "duration": "6 weeks",
        "topics": ["music", "arts"],
        "format": "course",
    },
    {
        "title": "Modern Art & Ideas",
        "provider": "MoMA (Coursera)",
        "url": "https://www.coursera.org/learn/modern-art-ideas",
        "level": "beginner",
        "description": "Modern art history from MoMA.",
        "duration": "5 weeks",
        "topics": ["arts", "history"],
        "format": "course",
    },

    # ------------------------------------------------------------------
    # Business / Finance / Accounting
    # ------------------------------------------------------------------
    {
        "title": "Introduction to Corporate Finance (Aswath Damodaran)",
        "provider": "NYU Stern (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLUkh9m2BorqnKWu0g5ZUps_CbQ-JGtbI9",
        "level": "intermediate",
        "description": "Damodaran's world-renowned corporate finance lectures.",
        "duration": "~40 hours",
        "topics": ["finance", "business", "chartered accountancy"],
        "format": "playlist",
    },
    {
        "title": "Valuation (Aswath Damodaran)",
        "provider": "NYU Stern (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLUkh9m2BorqnDGoMSb7uZKAmuqM3xTPMV",
        "level": "advanced",
        "description": "Damodaran's flagship valuation course.",
        "duration": "~40 hours",
        "topics": ["finance", "business", "chartered accountancy"],
        "format": "playlist",
    },
    {
        "title": "Financial Accounting Fundamentals",
        "provider": "University of Virginia (Coursera)",
        "url": "https://www.coursera.org/learn/uva-darden-financial-accounting",
        "level": "beginner",
        "description": "Darden's intro to financial accounting.",
        "duration": "4 weeks",
        "topics": ["accounting", "finance", "business", "chartered accountancy"],
        "format": "course",
    },
    {
        "title": "Introduction to Financial Accounting",
        "provider": "Wharton / Penn (Coursera)",
        "url": "https://www.coursera.org/learn/wharton-accounting",
        "level": "beginner",
        "description": "Wharton's intro to financial accounting.",
        "duration": "4 weeks",
        "topics": ["accounting", "finance", "business", "chartered accountancy"],
        "format": "course",
    },
    {
        "title": "ICAI CA Foundation Study Material",
        "provider": "ICAI (official)",
        "url": "https://www.icai.org/post/study-material-foundation",
        "level": "beginner",
        "description": "Official ICAI CA Foundation study material — the authoritative source for Chartered Accountancy in India.",
        "duration": "self-paced",
        "topics": ["chartered accountancy", "accounting", "business"],
        "format": "course",
    },
]


def filter_catalog(topics: list[str], level: str) -> list[dict]:
    tset = {t.lower() for t in topics}
    results = []
    for c in CURATED:
        ct = {t.lower() for t in c["topics"]}
        if tset & ct:
            results.append(c)
    matching = [c for c in results if c["level"] == level]
    others = [c for c in results if c["level"] != level]
    return matching + others
