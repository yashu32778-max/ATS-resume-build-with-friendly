import os
from flask import Flask, request, jsonify, render_template_string
from google import genai
import PyPDF2
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Use an environment variable for security
API_KEY = os.environ.get("AIzaSyCxhIG-zkkf83qdvmynPMScFYySVd1sd2Y") 
client = genai.Client(api_key=API_KEY)

# This defines the UI for your browser
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OptiScanATS | Resume Optimization Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #f8fafc;
            --accent: #4f46e5;
        }

        body { 
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, hsla(225, 100%, 94%, 1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225, 100%, 90%, 1) 0, transparent 50%), 
                radial-gradient(at 100% 0%, hsla(210, 100%, 92%, 1) 0, transparent 50%), 
                radial-gradient(at 0% 100%, hsla(240, 100%, 95%, 1) 0, transparent 50%), 
                radial-gradient(at 100% 100%, hsla(220, 100%, 92%, 1) 0, transparent 50%);
            background-attachment: fixed;
            min-height: 100vh;
            font-size: 16px; /* Optimized base font size */
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            background-color: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        }

        .scanning-animation { 
            animation: scan 2s infinite ease-in-out; 
        }

        @keyframes scan {
            0% { transform: translateY(-100%); opacity: 0; }
            50% { opacity: 1; }
            100% { transform: translateY(400%); opacity: 0; }
        }

        .metric-bar { transition: width 1.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
        
        .nav-glass {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
        }

        .animate-reveal {
            animation: reveal 0.6s ease-out forwards;
        }

        @keyframes reveal {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Improved legibility for lists and secondary text */
        .text-sm-compact { font-size: 0.9375rem; line-height: 1.6; }
        .text-xs-label { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; }
    </style>
</head>
<body class="text-slate-800 antialiased">

    <header class="nav-glass sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <div class="bg-indigo-600 w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg">
                    <i class="fas fa-microchip text-lg"></i>
                </div>
                <div>
                    <h1 class="text-xl font-black tracking-tight text-slate-900 leading-none">OptiScan<span class="text-indigo-600">ATS</span></h1>
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resume Optimization Engine</span>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-12">
        
        <!-- View: Editor -->
        <div id="editor-view" class="space-y-10">
            <div class="text-center max-w-2xl mx-auto mb-10">
                <h2 class="text-4xl font-black text-slate-900 mb-3 tracking-tight">ATS Analyser</h2>
                <p class="text-slate-500 text-lg">Advanced diagnostics for Applicant Tracking System compatibility.</p>
            </div>

            <!-- Role Selection Panel -->
            <div class="glass-card rounded-2xl p-8 flex flex-col md:flex-row items-center gap-6">
                <div class="flex items-center gap-3 text-indigo-600 bg-indigo-50 px-5 py-3 rounded-xl shrink-0">
                    <i class="fas fa-bullseye text-base"></i>
                    <span class="font-bold text-sm uppercase tracking-wide">Target Context</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                    <select id="company-select" onchange="updateRoles()" class="bg-white border-0 ring-1 ring-slate-200 text-slate-700 text-sm font-semibold rounded-xl focus:ring-2 focus:ring-indigo-500 block w-full p-4 outline-none shadow-sm transition-all appearance-none cursor-pointer">
                        <option value="">Select Company</option>
                        <optgroup label="Tech Giants">
                            <option value="google">Google</option>
                            <option value="apple">Apple</option>
                            <option value="meta">Meta</option>
                            <option value="netflix">Netflix</option>
                            <option value="nvidia">NVIDIA</option>
                        </optgroup>
                        <optgroup label="Innovation & Finance">
                            <option value="openai">OpenAI</option>
                            <option value="stripe">Stripe</option>
                            <option value="goldman">Goldman Sachs</option>
                            <option value="spacex">SpaceX</option>
                            <option value="tesla">Tesla</option>
                        </optgroup>
                    </select>
                    <select id="role-select" disabled onchange="fillJobDescription()" class="bg-white border-0 ring-1 ring-slate-200 text-slate-700 text-sm font-semibold rounded-xl focus:ring-2 focus:ring-indigo-500 block w-full p-4 outline-none disabled:opacity-50 shadow-sm transition-all appearance-none cursor-pointer">
                        <option value="">Select Role Category</option>
                    </select>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Job Description Input -->
                <div class="glass-card rounded-3xl shadow-xl border-white/40 overflow-hidden">
                    <div class="px-8 py-5 border-b border-slate-100/50 bg-white/30 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <i class="fas fa-scroll text-indigo-500 text-base"></i>
                            <span class="font-bold text-slate-700 text-sm uppercase tracking-wider">Corpus Analysis (JD)</span>
                        </div>
                    </div>
                    <div class="p-8">
                        <textarea id="jd-input" class="w-full h-80 p-5 text-sm bg-white/50 border border-slate-200/60 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 outline-none transition resize-none leading-relaxed" placeholder="Paste requirements here..."></textarea>
                    </div>
                </div>

                <!-- Resume Upload -->
                <div class="glass-card rounded-3xl shadow-xl border-white/40 overflow-hidden flex flex-col">
                    <div class="px-8 py-5 border-b border-slate-100/50 bg-white/30 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <i class="fas fa-file-invoice text-indigo-500 text-base"></i>
                            <span class="font-bold text-slate-700 text-sm uppercase tracking-wider">Document Input (Resume)</span>
                        </div>
                    </div>
                    <div class="p-8 flex-grow">
                        <div id="drop-zone" class="h-80 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-white/40 transition-all group" onclick="document.getElementById('resume-upload').click()">
                            <i class="fas fa-cloud-arrow-up text-4xl text-indigo-600 mb-5 group-hover:scale-110 transition-transform"></i>
                            <h3 class="font-bold text-slate-900 text-lg">Upload Dataset</h3>
                            <p class="text-sm text-slate-500 mt-2">Drag .txt file or click to browse.</p>
                            <input type="file" id="resume-upload" class="hidden" accept=".txt" onchange="handleFileUpload(event)">
                            <div id="file-indicator" class="hidden mt-6 px-5 py-3 bg-slate-900 rounded-xl text-xs text-white font-bold flex items-center gap-3 shadow-lg">
                                <i class="fas fa-check-circle text-green-400"></i>
                                <span id="file-name-text"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex justify-center pt-4">
                <button onclick="analyzeWithModel()" id="analyze-btn" class="bg-indigo-600 text-white px-12 py-5 rounded-2xl text-lg font-black tracking-wide hover:bg-indigo-700 transition-all shadow-xl hover:-translate-y-1 active:scale-95 flex items-center gap-3">
                    <i class="fas fa-bolt"></i> Execute Analysis
                </button>
            </div>
        </div>

        <!-- View: Loading -->
        <div id="loading-view" class="hidden py-40 text-center">
            <div class="inline-block relative w-24 h-28 bg-white border border-slate-100 rounded-2xl shadow-2xl mb-8 overflow-hidden">
                <div class="scanning-animation absolute w-full h-1.5 bg-indigo-500"></div>
                <div class="p-5 space-y-3 opacity-20">
                    <div class="h-2 w-full bg-slate-400 rounded-full"></div>
                    <div class="h-2 w-5/6 bg-slate-400 rounded-full"></div>
                    <div class="h-2 w-full bg-slate-400 rounded-full"></div>
                </div>
            </div>
            <h3 class="text-2xl font-black text-slate-900 tracking-tight">Simulating ATS Parsing...</h3>
            <p class="text-slate-500 mt-2">Cross-referencing datasets against institutional patterns.</p>
        </div>

        <!-- View: Results -->
        <div id="results-view" class="hidden space-y-10 animate-reveal">
            <div class="flex flex-col lg:flex-row gap-10">
                <!-- Sidebar -->
                <div class="lg:w-1/3">
                    <div class="glass-card p-10 rounded-[2.5rem] shadow-2xl text-center">
                        <h4 class="text-xs-label uppercase text-slate-400 mb-5">Calculated Match</h4>
                        <div id="score-text" class="text-7xl font-black text-indigo-600 mb-3 tracking-tighter">0%</div>
                        <div id="score-message" class="text-xs font-black text-indigo-700 mb-10 px-6 py-2 bg-indigo-50 rounded-full inline-block tracking-wider uppercase"></div>
                        
                        <div class="space-y-6 text-left">
                            <div id="breakdown-bars" class="space-y-6"></div>
                        </div>

                        <hr class="my-8 border-slate-100">
                        <button onclick="location.reload()" class="w-full bg-white border border-slate-200 text-slate-600 py-4 rounded-2xl font-black text-sm hover:bg-slate-50 transition flex items-center justify-center gap-3">
                            <i class="fas fa-arrow-left"></i> New Session
                        </button>
                    </div>
                </div>

                <!-- Main Analysis -->
                <div class="lg:w-2/3 space-y-8">
                    <!-- Warnings Section -->
                    <div id="drawbacks-card" class="glass-card rounded-[2rem] shadow-xl border-white/50 overflow-hidden hidden">
                        <div class="bg-red-50/50 px-10 py-5 border-b border-slate-100 flex items-center gap-4">
                            <i class="fas fa-exclamation-triangle text-red-500 text-lg"></i>
                            <h5 class="text-xs-label uppercase tracking-widest text-slate-800">Critical Risks & Errors</h5>
                        </div>
                        <div class="p-10">
                            <ul id="drawbacks-list" class="space-y-5 text-sm-compact"></ul>
                        </div>
                    </div>

                    <!-- Strategy Section -->
                    <div class="glass-card rounded-[2rem] shadow-xl border-white/50 overflow-hidden">
                        <div class="bg-indigo-50/50 px-10 py-5 border-b border-slate-100 flex items-center gap-4">
                            <i class="fas fa-chess-knight text-indigo-600 text-lg"></i>
                            <h5 class="text-xs-label uppercase tracking-widest text-slate-800">Optimization Roadmap</h5>
                        </div>
                        <div class="p-10">
                            <ul id="insights-list" class="grid grid-cols-1 md:grid-cols-2 gap-5"></ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        const jobPresets = {
            google: {
                "Software Engineer (L4)": "Systems design, Java, Go, cloud scalability, algorithmic optimization, distributed systems, unit testing, CI/CD.",
                "Site Reliability Engineer": "Linux internals, networking protocols, automation, incident management, Kubernetes, Python, Shell scripting, monitoring.",
                "Technical Program Manager": "Cross-functional leadership, technical roadmaps, Agile, SDLC, resource planning, stakeholder communication.",
                "Product Manager": "Product strategy, data-driven decisions, user-centric design, GTM roadmap, competitive analysis, SQL.",
                "Data Scientist": "Machine learning models, statistics, TensorFlow, Python, BigQuery, experimental design, A/B testing.",
                "UX Researcher": "User studies, qualitative analysis, usability testing, HCI, survey design, persona development.",
                "Solutions Architect": "Cloud architecture, Google Cloud Platform (GCP), enterprise security, migration strategies, client consultation."
            },
            apple: {
                "iOS Engineer": "Swift, SwiftUI, Core Animation, device performance, Objective-C, Cocoa Touch, App Store deployment, Xcode.",
                "Hardware Systems Engineer": "PCB design, high-speed signaling, power management, validation, electrical engineering, CAD, signal integrity.",
                "Machine Learning Research": "Computer vision, NLP, on-device AI, CoreML, PyTorch, algorithm efficiency, neural networks.",
                "Operations Manager": "Supply chain optimization, global logistics, manufacturing, cost analysis, quality control, vendor management.",
                "Creative Director": "Visual storytelling, brand identity, typography, motion design, design systems, Adobe Creative Suite.",
                "Embedded Systems Engineer": "C, C++, RTOS, device drivers, low-level firmware, ARM architecture, debugging.",
                "Product Marketing Manager": "Consumer behavior, GTM strategy, product launch, brand narrative, market research."
            },
            meta: {
                "Frontend Engineer": "React, GraphQL, accessibility, performance optimization, JavaScript, CSS architectures, Jest, Relay.",
                "Product Designer": "Product thinking, interaction design, prototyping, Figma, user research, design systems, visual hierarchy.",
                "Security Engineer": "Threat modeling, application security, infrastructure, incident response, cryptography, penetration testing.",
                "Strategic Partner Manager": "Partnerships, ecosystem growth, negotiation, business development, analytics, CRM, platform policy.",
                "Data Engineer": "Data pipelines, Hive, Presto, ETL, data modeling, SQL optimization, Spark, data warehousing.",
                "Research Scientist": "AI/ML research, publications, deep learning, PyTorch, academic rigor, large-scale data analysis.",
                "Production Engineer": "Scalability, Linux, automation, Python, C++, large-scale infrastructure, reliability."
            },
            netflix: {
                "Senior UI Engineer": "TypeScript, rendering performance, cinematic TV UI, architecture, Node.js, A/B testing at scale.",
                "Distributed Systems Engineer": "JVM optimization, chaos engineering, high-availability, microservices, AWS, Cassandra, Kafka.",
                "Content Analyst": "Metadata strategy, algorithm curation, data visualization, industry trends, Python, content lifecycle.",
                "Cloud Security": "AWS IAM, VPC security, serverless, Zero Trust, compliance, automation, risk assessment.",
                "Marketing Specialist": "Digital campaigns, social media strategy, brand positioning, global markets, ROI tracking.",
                "Data Analytics Manager": "Business intelligence, Tableau, SQL, data-driven storytelling, team leadership, forecasting.",
                "Infrastructure Engineer": "Cloud infrastructure, Terraform, Spinnaker, observability, cost efficiency, scalable networking."
            },
            nvidia: {
                "Deep Learning SW": "CUDA, TensorRT, GPU architecture, C++, parallel programming, computer vision, deep learning frameworks.",
                "ASIC Design Engineer": "Verilog, VHDL, RTL design, verification, FPGA, hardware acceleration, synthesis tools.",
                "Gaming Ecosystem": "DirectX, Vulkan, graphics rendering, driver development, shaders, C++, ray tracing.",
                "Autonomous Driving": "Sensor fusion, perception, path planning, ROS, real-time systems, C++, safety critical systems.",
                "Solution Architect": "AI infrastructure, data centers, high-performance computing, enterprise AI, CUDA integration.",
                "Developer Relations": "Technical advocacy, SDK support, community engagement, Python, C++, public speaking.",
                "System Software Engineer": "Kernel programming, drivers, virtualization, C, performance profiling, low-level debugging."
            },
            openai: {
                "Research Engineer": "Large Language Models (LLMs), scaling laws, distributed training, PyTorch, reinforcement learning (RLHF).",
                "Product Engineer": "API development, full-stack, Next.js, model integration, latency optimization, high-traffic systems.",
                "Trust & Safety": "Content moderation, policy development, ML classifiers, safety evaluations, bias mitigation.",
                "Infrastructure Engineer": "Kubernetes clusters, GPU orchestration, Azure, training efficiency, high-performance networking."
            },
            stripe: {
                "Software Engineer (Backend)": "Ruby, Java, Go, API design, financial systems, reliability, payment processing, transactional integrity.",
                "Account Executive": "B2B sales, fintech, revenue growth, negotiation, complex deal cycles, CRM.",
                "Risk Analyst": "Fraud detection, ML models, chargeback management, data analysis, risk mitigation strategies."
            },
            goldman: {
                "Quantitative Researcher": "Financial modeling, stochastic calculus, Python, C++, risk management, algorithmic trading.",
                "Investment Banking Analyst": "Financial valuation, M&A, DCF, financial statements, Excel modeling, client decks.",
                "Cyber Security": "Financial compliance, threat hunting, IAM, infrastructure security, network defense."
            },
            spacex: {
                "Starlink SW Engineer": "Network protocols, C++, Python, distributed systems, satellite communication, low-latency code.",
                "Propulsion Engineer": "Thermodynamics, fluid mechanics, CAD, manufacturing, material science, engine testing.",
                "Flight Controls": "Control theory, GNC, simulation, C++, real-time software, aerospace dynamics."
            }
        };

        const COMMON_TYPOS = {
            "manger": "Manager", "devoloper": "Developer", "enginer": "Engineer", 
            "experince": "Experience", "responisble": "Responsible", "managment": "Management"
        };

        let currentResumeText = "";

        const MODEL_WEIGHTS = {
            skillDepth: 0.25, projectImpact: 0.30, 
            learningAbility: 0.20, authenticity: 0.15, jdMatch: 0.10
        };

        function updateRoles() {
            const company = document.getElementById('company-select').value;
            const roleSelect = document.getElementById('role-select');
            roleSelect.innerHTML = '<option value="">Select Role Category</option>';
            if (company && jobPresets[company]) {
                roleSelect.disabled = false;
                Object.keys(jobPresets[company]).forEach(role => {
                    const option = document.createElement('option');
                    option.value = role; option.textContent = role;
                    roleSelect.appendChild(option);
                });
            } else { roleSelect.disabled = true; }
        }

        function fillJobDescription() {
            const company = document.getElementById('company-select').value;
            const role = document.getElementById('role-select').value;
            if (company && role) document.getElementById('jd-input').value = jobPresets[company][role];
        }

        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                currentResumeText = e.target.result;
                document.getElementById('file-name-text').innerText = file.name;
                document.getElementById('file-indicator').classList.remove('hidden');
            };
            reader.readAsText(file);
        }

        function runScoringModel(resume, jd) {
            const r = resume.toLowerCase();
            const j = jd.toLowerCase();
            
            let sDepth = 60;
            if (r.match(/architect|optimize|scalable|senior|lead|strategy|expert/g)) sDepth += 20;
            if (r.match(/framework|library|tool|stack/g)) sDepth += 10;
            
            let pImpact = 50;
            const metrics = r.match(/\d+%/g) || [];
            const money = r.match(/\$\d+/g) || [];
            pImpact += (metrics.length * 10) + (money.length * 10);
            if (r.match(/launched|delivered|built|solved|reduced|increased/g)) pImpact += 10;

            let lAbility = 70;
            if (r.match(/certification|course|side project|hackathon|blog|github/g)) lAbility += 20;

            let auth = 85;
            const buzzwords = r.match(/passionate|hardworking|team player|dynamic/g) || [];
            auth -= (buzzwords.length * 5);
            
            const hasLinkedIn = /linkedin\.com\/in\/[\w-]+/i.test(resume);
            if (!hasLinkedIn) auth -= 20;

            let jdMatch = 0;
            const requiredKeys = j.split(/\W+/).filter(w => w.length > 3).slice(0, 15);
            let missingKeys = [];
            requiredKeys.forEach(w => { 
                if (r.includes(w)) { jdMatch += (100 / requiredKeys.length); } else { missingKeys.push(w); }
            });

            let detectedTypos = [];
            Object.keys(COMMON_TYPOS).forEach(typo => {
                if (new RegExp(`\\b${typo}\\b`, 'i').test(resume)) detectedTypos.push(typo);
            });

            const raw = {
                skillDepth: Math.min(100, sDepth),
                projectImpact: Math.min(100, pImpact),
                learningAbility: Math.min(100, lAbility),
                authenticity: Math.max(0, auth),
                jdMatch: Math.min(100, jdMatch)
            };

            const weightedFinal = (
                (raw.skillDepth * MODEL_WEIGHTS.skillDepth) +
                (raw.projectImpact * MODEL_WEIGHTS.projectImpact) +
                (raw.learningAbility * MODEL_WEIGHTS.learningAbility) +
                (raw.authenticity * MODEL_WEIGHTS.authenticity) +
                (raw.jdMatch * MODEL_WEIGHTS.jdMatch)
            );

            return {
                total: Math.round(weightedFinal),
                breakdown: raw,
                insights: generateInsights(raw, r, missingKeys, detectedTypos, hasLinkedIn)
            };
        }

        function generateInsights(raw, r, missingKeys, detectedTypos, hasLinkedIn) {
            const insights = [];
            const drawbacks = [];

            if (detectedTypos.length > 0) drawbacks.push(`<strong>Potential Typos Found:</strong> Detected "${detectedTypos.join(', ')}". These trigger high-rejection flags in legacy ATS systems.`);
            if (!hasLinkedIn) drawbacks.push("<strong>Missing Social Proof:</strong> No LinkedIn URL detected. Verification signal is significantly diminished.");
            if (missingKeys.length > 2) drawbacks.push(`<strong>Keyword Gaps:</strong> Missing core competencies: ${missingKeys.slice(0, 3).join(', ')}.`);
            if (raw.projectImpact < 60) drawbacks.push("<strong>Impact Deficit:</strong> Low usage of quantifiable metrics (%, $, numbers). Recruitment algorithms prioritize performance indicators.");

            if (raw.jdMatch < 70) insights.push("Normalize specific technical terminology with the exact JD keywords.");
            if (raw.skillDepth < 75) insights.push("Use authoritative technical action verbs (e.g., Architected, Optimized).");
            if (raw.learningAbility < 80) insights.push("Explicitly list recent certifications or continuous learning platforms.");
            
            if (insights.length === 0) insights.push("Strategic alignment is strong. Ensure visual layout is machine-readable.");

            return { insights, drawbacks };
        }

        function analyzeWithModel() {
            const jd = document.getElementById('jd-input').value;
            if (!currentResumeText || !jd) return;

            document.getElementById('editor-view').classList.add('hidden');
            document.getElementById('loading-view').classList.remove('hidden');

            setTimeout(() => {
                const results = runScoringModel(currentResumeText, jd);
                displayResults(results);
            }, 1200);
        }

        function displayResults(results) {
            document.getElementById('loading-view').classList.add('hidden');
            document.getElementById('results-view').classList.remove('hidden');
            
            document.getElementById('score-text').innerText = `${results.total}%`;
            document.getElementById('score-message').innerText = results.total > 80 ? "Strategic Alignment High" : "Intervention Recommended";

            const bars = document.getElementById('breakdown-bars');
            bars.innerHTML = '';
            const labels = {
                skillDepth: "Skill Depth", projectImpact: "Impact Factor", 
                learningAbility: "Growth Velocity", authenticity: "Signal Quality", jdMatch: "Key Alignment"
            };

            Object.entries(results.breakdown).forEach(([key, val]) => {
                const row = document.createElement('div');
                row.innerHTML = `
                    <div class="flex justify-between text-xs-label mb-2 uppercase text-slate-400">
                        <span>${labels[key]}</span>
                        <span class="text-indigo-600">${Math.round(val)}%</span>
                    </div>
                    <div class="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                        <div class="bg-indigo-600 h-full metric-bar" style="width: 0%" data-width="${val}%"></div>
                    </div>
                `;
                bars.appendChild(row);
            });

            const draws = document.getElementById('drawbacks-card');
            const drawsList = document.getElementById('drawbacks-list');
            if (results.insights.drawbacks.length > 0) {
                draws.classList.remove('hidden');
                drawsList.innerHTML = results.insights.drawbacks.map(d => `<li class="flex items-start gap-4 text-slate-700 leading-relaxed"><i class="fas fa-times-circle text-red-500 mt-1.5 text-sm"></i> <span>${d}</span></li>`).join('');
            }

            const list = document.getElementById('insights-list');
            list.innerHTML = results.insights.insights.map(i => `
                <li class="p-6 bg-white/40 rounded-2xl border border-white/50 flex items-start gap-4 shadow-sm">
                    <i class="fas fa-arrow-circle-right text-green-500 mt-1 text-base"></i>
                    <p class="text-sm font-bold text-slate-800 leading-relaxed">${i}</p>
                </li>
            `).join('');

            setTimeout(() => {
                document.querySelectorAll('.metric-bar').forEach(bar => {
                    bar.style.width = bar.getAttribute('data-width');
                });
            }, 100);
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    # This renders the form when you visit 127.0.0.1:8080
    return render_template_string(HTML_TEMPLATE)

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    return text

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files or "job_description" not in request.form:
        return jsonify({"error": "Missing data"}), 400

    file = request.files["resume"]
    jd_text = request.form.get("job_description")

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(pdf_path)

    resume_text = extract_text_from_pdf(pdf_path)
    
    prompt = f"Analyze this resume: {resume_text} against this JD: {jd_text}. Return JSON: match_percentage, missing_skills, matching_skills."

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return response.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)