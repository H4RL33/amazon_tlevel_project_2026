"""
Idempotent seed script. Run via:
  poetry run python seed.py

Uses ON CONFLICT DO NOTHING for topics (slug is unique) and
WHERE NOT EXISTS for t_levels (no unique constraint on name).
Designed to be invoked as a one-off ECS task in production.
"""

import asyncio
import sys
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.embedding_service import embed_text

TOPICS = [
    {
        "slug": "digital-production-design-development",
        "name": "Digital Production, Design and Development",
        "description": "Learn to design, build, and test digital products including software, systems, and services.",
        "accent_colour": "#0066CC",
        "t_levels": [
            {
                "name": "Digital Production, Design and Development",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-business-services",
        "name": "Digital Business Services",
        "description": "Understand how digital tools and services support modern business operations.",
        "accent_colour": "#00994C",
        "t_levels": [
            {
                "name": "Digital Business Services",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-infrastructure",
        "name": "Digital Infrastructure",
        "description": "Explore the networks, cloud platforms, and systems that underpin digital services.",
        "accent_colour": "#CC3300",
        "t_levels": [
            {
                "name": "Digital Infrastructure",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "design-surveying-planning",
        "name": "Design, Surveying and Planning",
        "description": "Discover careers in built environment design, including architecture and civil engineering.",
        "accent_colour": "#996600",
        "t_levels": [
            {
                "name": "Design, Surveying and Planning for Construction",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and ideally a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "health",
        "name": "Health",
        "description": "Prepare for a career in healthcare, covering clinical environments and patient support.",
        "accent_colour": "#660099",
        "t_levels": [
            {
                "name": "Health (Nursing)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
            {
                "name": "Health (Midwifery)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
        ],
    },
]


ALBUMS = [
    # ── 1. Cloud Computing Fundamentals ─────────────────────────────────────────
    {
        "title": "Cloud Computing Fundamentals",
        "description": "An introduction to cloud computing, virtualisation, and "
        "the infrastructure that powers modern digital services.",
        "icon": "cloud",
        "t_level_topic_slug": "digital-infrastructure",
        "sides": [
            {
                "title": "Getting Started",
                "snippets": [
                    {
                        "title": "What is Cloud Computing?",
                        "body": "Cloud computing means renting computing power, storage, and "
                        "services over the internet instead of buying and running your own "
                        "physical servers. Providers like AWS offer this on demand, billed by "
                        "usage, so you can scale up or down as your needs change.",
                        "content_type": "article",
                    },
                    {
                        "title": "Cloud Service Models: IaaS, PaaS, SaaS",
                        "body": "Infrastructure as a Service (IaaS) rents raw virtual machines "
                        "and networking. Platform as a Service (PaaS) goes further, managing "
                        "the operating system and runtime so you just deploy code. Software "
                        "as a Service (SaaS) hands you a finished application — think Gmail "
                        "or Netflix — with nothing to install or manage at all.",
                        "content_type": "article",
                    },
                    {
                        "title": "Public, Private, and Hybrid Cloud",
                        "body": "A public cloud (like AWS or Azure) shares physical hardware "
                        "between many customers, kept isolated from each other. A private "
                        "cloud is dedicated to one organisation, often for stricter compliance "
                        "needs. A hybrid cloud combines both, letting a business keep "
                        "sensitive workloads private while bursting into public cloud "
                        "capacity when demand spikes.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Compute & Virtualisation",
                "snippets": [
                    {
                        "title": "Virtual Private Servers Explained",
                        "body": "A Virtual Private Server (VPS) is a virtual machine sold as a "
                        "service by a hosting provider. It behaves like a dedicated physical "
                        "server but is actually a partitioned slice of a larger physical "
                        "machine, shared with other VPS instances.",
                        "content_type": "article",
                    },
                    {
                        "title": "Servers vs Serverless",
                        "body": "Traditional servers run continuously and you pay for them "
                        "whether or not they're handling requests. Serverless computing runs "
                        "your code only when triggered, and you pay only for the compute time "
                        "actually used.",
                        "content_type": "article",
                    },
                    {
                        "title": "Containers and Docker Basics",
                        "body": "A container packages an application together with everything "
                        "it needs to run — code, libraries, settings — so it behaves "
                        "identically on any machine. Docker is the most widely used tool for "
                        "building and running containers, and container orchestrators like "
                        "Kubernetes or AWS ECS manage many containers running across a "
                        "cluster of servers.",
                        "content_type": "article",
                    },
                    {
                        "title": "Understanding Auto Scaling",
                        "body": "Auto scaling automatically adds or removes compute capacity "
                        "to match demand. If traffic spikes, more instances launch to share "
                        "the load; when traffic drops, idle instances are terminated to save "
                        "cost. This is one of the main reasons cloud computing can be cheaper "
                        "than buying fixed hardware for peak demand you rarely hit.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Networking & Security",
                "snippets": [
                    {
                        "title": "Intro to Virtual Private Networks",
                        "body": "A Virtual Private Network (VLAN) logically separates devices "
                        "on the same physical network into distinct broadcast domains, "
                        "improving security and organisation without needing separate "
                        "physical switches for each group.",
                        "content_type": "article",
                    },
                    {
                        "title": "How DNS Works",
                        "body": "The Domain Name System (DNS) translates human-readable "
                        "domain names like example.com into the numeric IP addresses "
                        "computers actually use to find each other. Without it, you'd have "
                        "to remember a string of numbers for every website you wanted to "
                        "visit.",
                        "content_type": "article",
                    },
                    {
                        "title": "Load Balancers Explained",
                        "body": "A load balancer sits in front of a group of servers and "
                        "distributes incoming requests across them, so no single server gets "
                        "overwhelmed. It also detects unhealthy servers and stops sending "
                        "them traffic, which is a major reason cloud applications can stay "
                        "online even when individual servers fail.",
                        "content_type": "article",
                    },
                    {
                        "title": "Cloud Security Fundamentals",
                        "body": "Cloud providers secure the physical infrastructure, but "
                        "customers are responsible for securing what they build on top of "
                        "it — this split is called the 'shared responsibility model'. Common "
                        "practices include encrypting data, tightly scoping permissions so "
                        "accounts can only access what they need, and never exposing "
                        "databases directly to the public internet.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Storage & Databases",
                "snippets": [
                    {
                        "title": "Object Storage vs Block Storage",
                        "body": "Block storage splits data into fixed-size chunks and is "
                        "typically attached to a single virtual machine, much like a hard "
                        "drive. Object storage (like Amazon S3) stores whole files as "
                        "objects with metadata, accessible over the internet from anywhere, "
                        "and is what most cloud applications use for images, videos, and "
                        "backups.",
                        "content_type": "article",
                    },
                    {
                        "title": "Relational vs NoSQL Databases",
                        "body": "Relational databases (like PostgreSQL) store data in tables "
                        "with strict, predefined relationships between them, enforced by a "
                        "schema. NoSQL databases trade some of that structure for "
                        "flexibility and scale, storing data as documents, key-value pairs, "
                        "or graphs instead — useful when your data doesn't fit neatly into "
                        "rows and columns.",
                        "content_type": "article",
                    },
                    {
                        "title": "Data Backups and Disaster Recovery",
                        "body": "A backup is a copy of your data kept somewhere separate, so "
                        "it can be restored if the original is lost or corrupted. Disaster "
                        "recovery goes further, planning for how an entire service recovers "
                        "from a major outage — for example, automatically failing over to a "
                        "backup region in a different part of the world.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Careers in Cloud Computing",
                "snippets": [
                    {
                        "title": "Day in the Life of a Cloud Engineer",
                        "body": "A cloud engineer designs, builds, and maintains the "
                        "infrastructure applications run on. A typical day might involve "
                        "writing infrastructure-as-code to provision new resources, "
                        "investigating why a service is running slowly, and reviewing "
                        "security permissions before a new feature goes live.",
                        "content_type": "article",
                    },
                    {
                        "title": "AWS, Azure, and Google Cloud: An Overview",
                        "body": "Amazon Web Services (AWS), Microsoft Azure, and Google Cloud "
                        "Platform (GCP) are the three largest cloud providers, each offering "
                        "broadly similar services — compute, storage, databases, "
                        "networking — under different names and pricing. Most cloud "
                        "engineering roles specialise in one provider, though the underlying "
                        "concepts transfer well between them.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 2. Python for Beginners ──────────────────────────────────────────────────
    {
        "title": "Python for Beginners",
        "description": "A practical introduction to Python programming — from your first "
        "script to writing reusable functions and understanding how data is stored.",
        "icon": "code",
        "t_level_topic_slug": "digital-production-design-development",
        "sides": [
            {
                "title": "Getting Started",
                "snippets": [
                    {
                        "title": "What is Python?",
                        "body": "Python is a high-level, general-purpose programming language "
                        "created by Guido van Rossum and first released in 1991. It is "
                        "designed to be readable — its syntax is close to plain English, "
                        "which makes it easier for beginners to learn. Python is used across "
                        "an enormous range of tasks: building websites and APIs, automating "
                        "repetitive work, analysing data, and training machine learning "
                        "models. It consistently ranks as one of the most popular programming "
                        "languages in developer surveys, and is the most widely taught "
                        "language in UK schools and universities.",
                        "content_type": "article",
                    },
                    {
                        "title": "Setting Up Your Python Environment",
                        "body": "Before you can write Python, you need a way to run it. "
                        "Download and install Python from python.org — once installed you can "
                        "run it interactively in a terminal by typing `python3`. For writing "
                        "longer programs, most developers use a code editor: VS Code is a "
                        "popular free option, and its Python extension gives you syntax "
                        "highlighting, auto-complete, and a built-in debugger. Online tools "
                        "like Replit or Google Colab let you write and run Python directly in "
                        "a web browser without installing anything, which is a quick way to "
                        "experiment when you're just starting out.",
                        "content_type": "article",
                    },
                    {
                        "title": "Your First Python Program",
                        "body": "The traditional starting point for learning any programming "
                        "language is printing the phrase 'Hello, World!' on screen. In Python "
                        "this is a single line: `print('Hello, World!')`. The `print()` "
                        "function outputs text to the terminal. You can change the text inside "
                        "the quotes to print anything you like. A next step is storing a name "
                        "in a variable and printing a personalised greeting: set "
                        "`name = 'Alex'` then `print(f'Hello, {name}!')`. The `f` prefix "
                        "creates a formatted string that substitutes the variable's value "
                        "directly into the text at the point of the curly braces.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Core Data Types",
                "snippets": [
                    {
                        "title": "Strings, Integers, and Floats",
                        "body": "Python stores data in types that reflect what the value "
                        "represents. A string is a piece of text, written inside single or "
                        "double quotes — for example `'hello'` or `'123'`. An integer is a "
                        "whole number with no decimal point, like `42`. A float is a number "
                        "with a decimal point, like `3.14`. Python infers the type "
                        "automatically when you assign a value to a variable, so you rarely "
                        "need to declare types manually. You can check a value's type with "
                        "the built-in `type()` function: `type(42)` returns `<class 'int'>` "
                        "and `type('hi')` returns `<class 'str'>`.",
                        "content_type": "article",
                    },
                    {
                        "title": "Lists and Tuples",
                        "body": "A list in Python is an ordered collection of values, written "
                        "as a comma-separated sequence inside square brackets — for example "
                        "`fruits = ['apple', 'banana', 'cherry']`. Lists are mutable, meaning "
                        "you can add, remove, or change items after creation. A tuple looks "
                        "similar but uses round brackets: `coords = (51.5, -0.1)`. Tuples are "
                        "immutable — once created their contents cannot change — which makes "
                        "them useful for fixed data like coordinates or RGB colour values. You "
                        "access items in both by index, starting from zero: `fruits[0]` "
                        "returns `'apple'`.",
                        "content_type": "article",
                    },
                    {
                        "title": "Dictionaries and Sets",
                        "body": "A dictionary stores data as key-value pairs inside curly "
                        "braces: `person = {'name': 'Anya', 'age': 17}`. You access values "
                        "by their key: `person['name']` returns `'Anya'`. Dictionaries are "
                        "useful for structured records and are the Python equivalent of a "
                        "JSON object. A set is also written with curly braces but stores only "
                        "unique, unordered values — useful for removing duplicates or "
                        "checking membership quickly. `my_set = {1, 2, 3, 2, 1}` stores only "
                        "`{1, 2, 3}` because duplicates are discarded automatically.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Control Flow & Loops",
                "snippets": [
                    {
                        "title": "If Statements and Boolean Logic",
                        "body": "An if statement runs a block of code only when a condition "
                        "is true. In Python: `if score >= 50: print('Pass')`. Indentation "
                        "defines the block — everything indented under the `if` belongs to "
                        "it. You can add `else` for when the condition is false, or `elif` "
                        "for additional conditions. Conditions use comparison operators like "
                        "`==`, `!=`, `>`, `<`, `>=`, and `<=`. You can combine conditions "
                        "with `and`, `or`, and `not`: `if age >= 13 and age < 18:` matches "
                        "any teenager. Python evaluates conditions from left to right and "
                        "stops as soon as the result is determined.",
                        "content_type": "article",
                    },
                    {
                        "title": "For Loops and Ranges",
                        "body": "A for loop repeats a block of code for each item in a "
                        "sequence. `for fruit in fruits: print(fruit)` prints each item in "
                        "the `fruits` list on its own line. The `range()` function generates "
                        "a sequence of numbers — `range(5)` produces 0, 1, 2, 3, 4 — making "
                        "it straightforward to repeat something a fixed number of times: "
                        "`for i in range(10): print(i)`. You can also loop over the "
                        "characters in a string or the keys in a dictionary. Loops are one "
                        "of the most fundamental constructs in any programming language and "
                        "are used constantly in real Python code.",
                        "content_type": "article",
                    },
                    {
                        "title": "While Loops and Break",
                        "body": "A while loop repeats a block of code for as long as a "
                        "condition remains true. `while count < 10: count += 1` increments "
                        "`count` until it reaches 10. If the condition never becomes false "
                        "the loop runs forever — an infinite loop, which is usually a bug. "
                        "The `break` statement immediately exits a loop when executed, and "
                        "`continue` skips the rest of the current iteration and moves to the "
                        "next one. While loops are useful when you don't know in advance how "
                        "many iterations you'll need, such as reading input until the user "
                        "types a specific command.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Functions & Scope",
                "snippets": [
                    {
                        "title": "Defining and Calling Functions",
                        "body": "A function is a named, reusable block of code. You define "
                        "one with the `def` keyword: `def greet(name): print(f'Hello, "
                        "{name}!')`. You call it by name followed by parentheses: "
                        "`greet('Sam')`. Functions help you avoid repeating the same logic "
                        "in multiple places — if you need to change behaviour, you change it "
                        "in one place and all callers benefit immediately. Good functions do "
                        "one thing clearly and are named with a descriptive verb phrase, like "
                        "`calculate_total` or `send_email`. Python's standard library "
                        "provides thousands of built-in functions, and packages like NumPy "
                        "and Requests extend this further.",
                        "content_type": "article",
                    },
                    {
                        "title": "Parameters, Arguments, and Return Values",
                        "body": "A parameter is a variable in a function's definition that "
                        "accepts an input value. An argument is the actual value you pass "
                        "when calling it. In `def add(a, b):`, `a` and `b` are parameters; "
                        "in `add(3, 4)`, 3 and 4 are the arguments. A function sends a "
                        "result back to the caller using the `return` statement: "
                        "`def add(a, b): return a + b`. The caller can then store this: "
                        "`total = add(3, 4)`. Functions without a `return` statement "
                        "implicitly return `None`. Default parameter values let you make "
                        "arguments optional: `def greet(name='World'):` means `greet()` "
                        "works fine with no argument passed.",
                        "content_type": "article",
                    },
                    {
                        "title": "Variable Scope and Namespaces",
                        "body": "Scope describes which parts of your code can see a particular "
                        "variable. A variable created inside a function is local — it only "
                        "exists while the function runs and cannot be seen from outside. A "
                        "variable defined at the top level of a script is global — visible "
                        "everywhere in that file. When Python encounters a name it looks "
                        "first in the local scope, then in enclosing functions, then "
                        "globally, then in built-ins — this order is called the LEGB rule. "
                        "Modifying global variables from inside functions is possible but "
                        "generally considered poor practice; passing values in as arguments "
                        "and returning new values out is cleaner and easier to test.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 3. Cybersecurity Essentials ──────────────────────────────────────────────
    {
        "title": "Cybersecurity Essentials",
        "description": "Explore the threats that target digital systems, how encryption and "
        "authentication protect data, and the skills needed to build a career in security.",
        "icon": "shield",
        "t_level_topic_slug": "digital-infrastructure",
        "sides": [
            {
                "title": "The Threat Landscape",
                "snippets": [
                    {
                        "title": "Types of Cyber Attacks",
                        "body": "Cyber attacks take many forms, but most aim to steal data, "
                        "disrupt services, or gain unauthorised access to systems. Common "
                        "attack types include phishing (tricking people into revealing "
                        "credentials), denial-of-service (overwhelming a server with traffic "
                        "until it goes offline), man-in-the-middle (intercepting "
                        "communications between two parties), and SQL injection (inserting "
                        "malicious database commands into a web form). Understanding the "
                        "range of attack types is the starting point for building defences, "
                        "since you can't protect against what you don't recognise.",
                        "content_type": "article",
                    },
                    {
                        "title": "Social Engineering and Phishing",
                        "body": "Social engineering attacks manipulate people rather than "
                        "exploiting technical vulnerabilities. Phishing emails impersonate "
                        "trusted organisations — banks, delivery companies, or IT support — "
                        "to trick recipients into clicking a malicious link or entering "
                        "credentials on a fake website. Spear phishing targets specific "
                        "individuals using personal details gathered from social media. "
                        "Vishing uses phone calls and smishing uses text messages. Technical "
                        "controls can filter many of these attempts, but user awareness "
                        "training remains one of the most effective defences, since attackers "
                        "frequently bypass technical layers by exploiting human trust.",
                        "content_type": "article",
                    },
                    {
                        "title": "Malware: Viruses, Ransomware, and Spyware",
                        "body": "Malware is any software designed to harm a system or steal "
                        "data. A virus attaches itself to legitimate files and spreads when "
                        "those files are shared. A worm spreads across networks without "
                        "needing a host file. Ransomware encrypts a victim's files and "
                        "demands payment for the decryption key — high-profile attacks have "
                        "paralysed hospitals and local councils. Spyware silently monitors "
                        "activity and sends data to an attacker, while adware generates "
                        "unwanted adverts. A trojan disguises itself as legitimate software "
                        "to gain the user's trust before executing its malicious payload.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Encryption & Authentication",
                "snippets": [
                    {
                        "title": "How Encryption Works",
                        "body": "Encryption transforms readable data into an unreadable format "
                        "using a mathematical algorithm and a key, so that only someone with "
                        "the correct key can reverse the process. Symmetric encryption uses "
                        "the same key to encrypt and decrypt, making it fast but requiring a "
                        "secure way to share that key. Asymmetric encryption uses a pair of "
                        "mathematically linked keys: a public key (shared freely) and a "
                        "private key (kept secret). Data encrypted with the public key can "
                        "only be decrypted with the private key. HTTPS uses asymmetric "
                        "encryption to establish a secure session before switching to faster "
                        "symmetric encryption for the rest of the connection.",
                        "content_type": "article",
                    },
                    {
                        "title": "Passwords and Multi-Factor Authentication",
                        "body": "A strong password is long (12+ characters), random, and "
                        "unique to each service. Reusing the same password across sites means "
                        "a breach at one service can expose all the others. A password "
                        "manager generates and stores strong unique passwords so you only "
                        "need to remember one master password. Multi-factor authentication "
                        "(MFA) adds a second verification step after the password — typically "
                        "a time-based code from an authenticator app or a hardware key. Even "
                        "if an attacker steals your password, MFA prevents them from logging "
                        "in without also having your second factor.",
                        "content_type": "article",
                    },
                    {
                        "title": "Public Key Infrastructure",
                        "body": "Public Key Infrastructure (PKI) is the system of digital "
                        "certificates, certificate authorities, and processes that enable "
                        "trusted communication over the internet. A certificate authority "
                        "(CA) is a trusted organisation that issues digital certificates "
                        "binding a public key to an identity — for example, confirming that "
                        "the public key for example.com genuinely belongs to that domain. "
                        "When your browser shows a padlock, it means the site presented a "
                        "certificate signed by a CA your browser trusts. Without PKI, anyone "
                        "could intercept traffic and present their own public key, pretending "
                        "to be the intended destination.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Defending Systems",
                "snippets": [
                    {
                        "title": "Firewalls and Intrusion Detection",
                        "body": "A firewall filters network traffic according to rules — "
                        "permitting or blocking packets based on source, destination, port, "
                        "and protocol. A network firewall sits at the perimeter of a network; "
                        "a host-based firewall runs on individual machines. An intrusion "
                        "detection system (IDS) monitors traffic or system activity for "
                        "suspicious patterns and raises alerts. An intrusion prevention "
                        "system (IPS) goes further and can actively block suspect traffic. "
                        "Together these controls form a layered defence — if an attacker "
                        "bypasses one layer, they still face others. This principle of "
                        "multiple overlapping controls is called defence in depth.",
                        "content_type": "article",
                    },
                    {
                        "title": "Patch Management and Updates",
                        "body": "Software vulnerabilities are discovered regularly — sometimes "
                        "by researchers, sometimes by attackers first. Vendors release patches "
                        "to fix known vulnerabilities, but systems only benefit from those "
                        "fixes once the patches are applied. Patch management is the process "
                        "of keeping software up to date in a controlled way: testing patches "
                        "before deploying to production, prioritising critical security fixes, "
                        "and tracking what version runs on every system. Many major breaches "
                        "have exploited vulnerabilities for which patches had been available "
                        "for months or years before the attack. Timely patching removes a "
                        "large proportion of an attacker's available footholds.",
                        "content_type": "article",
                    },
                    {
                        "title": "Incident Response Basics",
                        "body": "An incident response plan sets out how an organisation "
                        "detects, contains, and recovers from a security breach. The typical "
                        "phases are: preparation (having tools and playbooks ready), "
                        "identification (detecting that an incident has occurred), "
                        "containment (stopping the attacker from spreading further), "
                        "eradication (removing the attacker and their tools), recovery "
                        "(restoring systems to normal operation), and lessons learned (reviewing "
                        "what happened to prevent recurrence). Fast, practised response "
                        "significantly reduces the impact of a breach. Regular drills and "
                        "tabletop exercises keep teams prepared before a real incident occurs.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Careers in Cybersecurity",
                "snippets": [
                    {
                        "title": "Roles in the Security Industry",
                        "body": "Cybersecurity encompasses a wide range of job roles. Security "
                        "analysts monitor systems for threats and investigate alerts. Penetration "
                        "testers (pen testers) are paid to attempt to break into systems before "
                        "real attackers do. Security engineers design and build defensive "
                        "infrastructure. Threat intelligence analysts track adversary groups "
                        "and their techniques. Security operations centre (SOC) analysts work "
                        "shifts responding to live threats. At a senior level, a Chief "
                        "Information Security Officer (CISO) sets an organisation's overall "
                        "security strategy. UK demand for security professionals continues to "
                        "outstrip supply, making it a strong career choice.",
                        "content_type": "article",
                    },
                    {
                        "title": "Ethical Hacking and Penetration Testing",
                        "body": "Ethical hacking means deliberately attempting to breach a "
                        "system's defences with the owner's permission, in order to find "
                        "weaknesses before malicious attackers do. A penetration test is a "
                        "structured engagement in which a tester tries to gain unauthorised "
                        "access using the same techniques a real attacker might use — "
                        "reconnaissance, exploitation, privilege escalation, and lateral "
                        "movement. The tester documents every vulnerability found and reports "
                        "it to the organisation with recommended fixes. Ethical hacking "
                        "requires written authorisation and a clearly defined scope, and "
                        "operates within strict legal and professional boundaries.",
                        "content_type": "article",
                    },
                    {
                        "title": "Certifications and Learning Paths",
                        "body": "Several well-recognised certifications mark progress in a "
                        "cybersecurity career. CompTIA Security+ is widely considered the "
                        "entry-level benchmark and covers core defensive concepts. Certified "
                        "Ethical Hacker (CEH) focuses on offensive techniques used in "
                        "penetration testing. OSCP (Offensive Security Certified Professional) "
                        "is a hands-on exam requiring candidates to compromise real machines. "
                        "For blue-team and governance roles, CISSP and CISM are well regarded "
                        "at a senior level. Beyond certifications, platforms like Hack The Box "
                        "and TryHackMe offer practical, gamified labs where you can develop "
                        "hands-on skills at your own pace.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 4. Web Development Fundamentals ─────────────────────────────────────────
    {
        "title": "Web Development Fundamentals",
        "description": "Learn how the web is built — from HTML structure and CSS styling to "
        "JavaScript interactivity and the accessibility principles that make sites usable for everyone.",
        "icon": "globe",
        "t_level_topic_slug": "digital-production-design-development",
        "sides": [
            {
                "title": "HTML Foundations",
                "snippets": [
                    {
                        "title": "What is HTML?",
                        "body": "HTML — HyperText Markup Language — is the standard language "
                        "used to structure content on the web. Every web page you visit is, "
                        "at its core, an HTML document. HTML uses tags (keywords wrapped in "
                        "angle brackets) to describe elements: `<h1>` marks a top-level "
                        "heading, `<p>` marks a paragraph, and `<a>` marks a hyperlink. "
                        "Browsers parse these tags and render them visually for the user. "
                        "HTML alone handles structure and meaning; it is CSS that controls "
                        "visual appearance, and JavaScript that adds interactive behaviour. "
                        "Together these three technologies form the foundation of every "
                        "website and web application.",
                        "content_type": "article",
                    },
                    {
                        "title": "Document Structure and Semantic Tags",
                        "body": "Every HTML document follows a standard structure: a `<!DOCTYPE "
                        "html>` declaration, an `<html>` root element, a `<head>` (containing "
                        "metadata like the page title and linked stylesheets) and a `<body>` "
                        "(containing the visible content). Semantic tags give meaning to "
                        "sections of the page: `<header>`, `<nav>`, `<main>`, `<article>`, "
                        "`<section>`, `<aside>`, and `<footer>` describe what each block "
                        "represents, not just how it looks. Screen readers use these tags to "
                        "help visually impaired users navigate the page, and search engines "
                        "use them to understand page structure — making semantic HTML both an "
                        "accessibility and an SEO concern.",
                        "content_type": "article",
                    },
                    {
                        "title": "Links, Images, and Forms",
                        "body": "The `<a>` tag creates a hyperlink: "
                        "`<a href='https://example.com'>Click here</a>`. The `href` attribute "
                        "specifies the destination URL. The `<img>` tag embeds an image: "
                        "`<img src='photo.jpg' alt='A description'>`. The `alt` attribute "
                        "provides a text alternative for screen readers and for browsers that "
                        "cannot display the image — it is mandatory for accessibility. Forms "
                        "collect user input using `<form>`, `<input>`, `<select>`, and "
                        "`<button>` elements. When a form is submitted, the browser sends the "
                        "data to a server (or handles it with JavaScript), making forms the "
                        "primary way users interact with web applications.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Styling with CSS",
                "snippets": [
                    {
                        "title": "Selectors, Properties, and the Box Model",
                        "body": "CSS — Cascading Style Sheets — controls the visual "
                        "presentation of HTML. A CSS rule consists of a selector (which "
                        "elements to target) and a declaration block (the styles to apply): "
                        "`p { color: navy; font-size: 1rem; }`. Every HTML element is "
                        "modelled as a rectangular box with four layers: the content area, "
                        "padding (space between content and border), border, and margin "
                        "(space outside the border). Understanding the box model is essential "
                        "for controlling layout and spacing. The `box-sizing: border-box` "
                        "declaration makes width and height include padding and border, which "
                        "most developers find more intuitive to work with.",
                        "content_type": "article",
                    },
                    {
                        "title": "Flexbox and Grid Layouts",
                        "body": "Flexbox is a CSS layout model designed for arranging items "
                        "in a row or column. Setting `display: flex` on a container lets its "
                        "children grow, shrink, and align relative to each other, making it "
                        "straightforward to build navigation bars, card rows, and centred "
                        "layouts. CSS Grid is a two-dimensional system for building more "
                        "complex page layouts with rows and columns. `display: grid` combined "
                        "with `grid-template-columns` and `grid-template-rows` defines the "
                        "structure. The two systems are complementary — Grid is usually used "
                        "for overall page structure and Flexbox for arranging components "
                        "within each area.",
                        "content_type": "article",
                    },
                    {
                        "title": "Responsive Design with Media Queries",
                        "body": "A responsive website adapts its layout to suit different "
                        "screen sizes — from a phone to a tablet to a desktop monitor. CSS "
                        "media queries apply different rules based on the device's "
                        "characteristics: `@media (max-width: 768px) { ... }` targets screens "
                        "narrower than 768 pixels. A mobile-first approach writes base styles "
                        "for small screens and uses media queries to progressively enhance "
                        "the layout for larger ones. The CSS `clamp()` function and relative "
                        "units like `rem`, `em`, `%`, and `vw` (viewport width) further "
                        "help elements scale fluidly rather than snapping between fixed "
                        "breakpoints.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "JavaScript Basics",
                "snippets": [
                    {
                        "title": "Variables, Functions, and Events",
                        "body": "JavaScript adds interactive behaviour to web pages. Variables "
                        "store values — `const name = 'Alex'` declares an immutable binding "
                        "and `let count = 0` declares one that can be reassigned. Functions "
                        "group reusable logic: `function add(a, b) { return a + b; }`. Event "
                        "listeners respond to user actions: "
                        "`button.addEventListener('click', () => { count += 1; })` runs code "
                        "whenever the button is clicked. Arrow functions (`() => {}`) are a "
                        "concise modern syntax for writing function expressions. Together, "
                        "variables, functions, and events are the core building blocks for "
                        "making pages respond to user input.",
                        "content_type": "article",
                    },
                    {
                        "title": "Manipulating the DOM",
                        "body": "The DOM (Document Object Model) is a programming interface "
                        "that represents an HTML page as a tree of objects, allowing "
                        "JavaScript to read and modify its content, structure, and styles. "
                        "`document.querySelector('#title')` finds the element with the id "
                        "'title'. `element.textContent = 'New text'` changes its visible "
                        "text. `element.style.color = 'red'` changes its CSS inline style. "
                        "`element.classList.add('active')` adds a CSS class. "
                        "`document.createElement('p')` creates a new element and "
                        "`parent.appendChild(child)` inserts it into the page. DOM "
                        "manipulation is how JavaScript dynamically updates what the user "
                        "sees without reloading the page.",
                        "content_type": "article",
                    },
                    {
                        "title": "Fetch API and Async JavaScript",
                        "body": "Web applications frequently need to retrieve data from a "
                        "server without reloading the page. The Fetch API makes HTTP requests "
                        "from JavaScript: `fetch('/api/users').then(r => r.json()).then("
                        "data => console.log(data))`. Because network requests take time, "
                        "they are asynchronous — the browser continues running other code "
                        "while waiting for the response. The `async/await` syntax makes "
                        "asynchronous code easier to read: `const data = await fetch(url)"
                        ".then(r => r.json())`. Understanding async programming is essential "
                        "for building any modern web application that communicates with an "
                        "API or database.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Accessibility & Best Practices",
                "snippets": [
                    {
                        "title": "Why Web Accessibility Matters",
                        "body": "Web accessibility means building sites that everyone can use, "
                        "including people with visual, hearing, motor, or cognitive "
                        "impairments. In the UK, the Equality Act 2010 requires public and "
                        "many commercial websites to be accessible — sites that aren't risk "
                        "legal action. Beyond compliance, accessible sites reach a wider "
                        "audience and are generally easier for everyone to use. Core "
                        "accessibility requirements include sufficient colour contrast, "
                        "keyboard-navigable interfaces, meaningful alternative text for "
                        "images, and captions for video content. Accessibility auditing tools "
                        "like axe and Lighthouse can automatically detect many common issues.",
                        "content_type": "article",
                    },
                    {
                        "title": "ARIA Roles and Keyboard Navigation",
                        "body": "ARIA (Accessible Rich Internet Applications) attributes "
                        "supplement HTML with extra accessibility information for screen "
                        "readers. `role='button'` tells screen readers an element acts as a "
                        "button; `aria-label='Close menu'` provides a text name for elements "
                        "without visible labels; `aria-expanded='true'` communicates the "
                        "state of expandable components. Keyboard navigation requires that "
                        "every interactive element can be reached with the Tab key and "
                        "activated with Enter or Space. Focus indicators — the visible "
                        "outline around a focused element — must never be hidden with "
                        "`outline: none` unless replaced with an equally visible alternative.",
                        "content_type": "article",
                    },
                    {
                        "title": "Performance and Page Speed",
                        "body": "Page load speed directly affects user experience and search "
                        "engine ranking. Key performance improvements include compressing and "
                        "correctly sizing images (modern formats like WebP and AVIF are "
                        "significantly smaller than JPEG or PNG), minifying CSS and "
                        "JavaScript to reduce file sizes, serving assets via a Content "
                        "Delivery Network (CDN) so they load from servers close to the user, "
                        "and deferring non-critical scripts so they don't block the initial "
                        "render. Google's Core Web Vitals — metrics for loading speed, "
                        "interactivity, and visual stability — are a useful framework for "
                        "measuring and improving real-world page performance.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 5. Data & AI Literacy ────────────────────────────────────────────────────
    {
        "title": "Data & AI Literacy",
        "description": "Understand how data is collected and prepared, how machine learning "
        "models are trained, and how AI is used — and misused — in the modern workplace.",
        "icon": "chart",
        "t_level_topic_slug": "digital-business-services",
        "sides": [
            {
                "title": "Understanding Data",
                "snippets": [
                    {
                        "title": "Types of Data and Where It Comes From",
                        "body": "Data is information recorded in a form that can be stored "
                        "and processed. Structured data fits neatly into tables — think a "
                        "spreadsheet of customer orders. Unstructured data has no fixed "
                        "format — emails, images, and social media posts are examples. "
                        "Semi-structured data sits between the two; JSON and XML files have "
                        "some structure but are more flexible than a relational table. Data "
                        "comes from many sources: user interactions on websites, IoT sensors, "
                        "transaction records, survey responses, and third-party data providers. "
                        "Understanding what data you have and where it originates is the "
                        "first step in any data analysis or machine learning project.",
                        "content_type": "article",
                    },
                    {
                        "title": "Cleaning and Preparing Data",
                        "body": "Raw data collected from real-world sources is rarely clean "
                        "enough to use directly. Common problems include missing values "
                        "(a survey respondent left a field blank), duplicate records, "
                        "inconsistent formatting (dates written as 01/06/25 in some rows and "
                        "1 June 2025 in others), and outliers that may be errors or genuinely "
                        "extreme observations. Data cleaning — identifying and correcting "
                        "these issues — typically takes the majority of time in a data project. "
                        "After cleaning, data often needs to be transformed: normalising "
                        "numeric ranges, encoding categorical variables as numbers, or "
                        "joining multiple datasets together before analysis can begin.",
                        "content_type": "article",
                    },
                    {
                        "title": "Visualising Data Effectively",
                        "body": "A well-chosen chart can communicate a pattern or insight "
                        "instantly; a poorly chosen one can mislead. Bar charts compare "
                        "values across categories. Line charts show how values change over "
                        "time. Scatter plots reveal relationships between two numeric "
                        "variables. Pie charts work for proportions but are often harder to "
                        "read than a bar chart showing the same data. Heatmaps use colour to "
                        "show the magnitude of values in a grid. Key principles: always label "
                        "axes with units, choose a colour scale accessible to colour-blind "
                        "readers, and avoid truncating the y-axis in ways that exaggerate "
                        "small differences.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "How Machine Learning Works",
                "snippets": [
                    {
                        "title": "Supervised vs Unsupervised Learning",
                        "body": "In supervised learning, a model is trained on labelled "
                        "examples — data where the correct answer is already known. For "
                        "instance, a spam filter trained on emails labelled 'spam' or 'not "
                        "spam' learns to classify new, unseen emails. In unsupervised "
                        "learning, the training data has no labels and the model discovers "
                        "structure by itself — clustering customers into groups with similar "
                        "purchasing behaviour is an example. Reinforcement learning is a "
                        "third paradigm where an agent learns by taking actions and receiving "
                        "rewards or penalties, used in game-playing AI and robotics. Most "
                        "practical business applications use supervised learning.",
                        "content_type": "article",
                    },
                    {
                        "title": "Training, Testing, and Overfitting",
                        "body": "Training a model means adjusting its internal parameters so "
                        "its predictions match the labelled training examples as closely as "
                        "possible. But a model that memorises the training data rather than "
                        "learning general patterns will perform poorly on new, unseen data — "
                        "this is overfitting. To detect overfitting, data is split into a "
                        "training set (used to train the model) and a test set (held back and "
                        "used to evaluate it). A large gap between training accuracy and test "
                        "accuracy is a sign of overfitting. Techniques to reduce it include "
                        "using more training data, regularisation, and simplifying the model.",
                        "content_type": "article",
                    },
                    {
                        "title": "Neural Networks Explained",
                        "body": "A neural network is a type of machine learning model loosely "
                        "inspired by the structure of a biological brain. It consists of "
                        "layers of interconnected nodes (neurons). The input layer receives "
                        "the raw data, hidden layers transform it through a series of "
                        "weighted calculations, and the output layer produces a prediction. "
                        "Deep neural networks have many hidden layers and can learn very "
                        "complex patterns from large amounts of data — this is what deep "
                        "learning means. Modern language models are extremely large deep "
                        "neural networks trained on vast text datasets. The same fundamental "
                        "architecture underlies image recognition, speech synthesis, and "
                        "translation tools.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "AI in Practice",
                "snippets": [
                    {
                        "title": "Natural Language Processing",
                        "body": "Natural Language Processing (NLP) is the branch of AI "
                        "concerned with enabling computers to understand, generate, and "
                        "respond to human language. Applications include chatbots and virtual "
                        "assistants, automatic translation, sentiment analysis (determining "
                        "whether a review is positive or negative), document summarisation, "
                        "and spam filtering. Large language models (LLMs) are trained on "
                        "enormous text corpora and can generate fluent prose, answer "
                        "questions, write code, and follow complex instructions. NLP "
                        "capabilities have advanced dramatically since the introduction of "
                        "the transformer architecture in 2017, making it one of the most "
                        "rapidly evolving areas of applied AI.",
                        "content_type": "article",
                    },
                    {
                        "title": "Computer Vision Applications",
                        "body": "Computer vision enables machines to interpret images and "
                        "video. Object detection identifies and locates specific items within "
                        "an image — used in security cameras, self-driving vehicles, and "
                        "product quality control. Image classification assigns a label to an "
                        "entire image. Facial recognition matches faces against a database of "
                        "known individuals. Medical imaging AI assists radiologists by "
                        "flagging anomalies in X-rays and scans. Optical character "
                        "recognition (OCR) extracts text from photographs of documents. "
                        "These systems are trained on large labelled image datasets and "
                        "typically use convolutional neural networks, architectures well "
                        "suited to processing spatial data.",
                        "content_type": "article",
                    },
                    {
                        "title": "AI Tools in the Workplace",
                        "body": "AI tools are increasingly embedded in everyday software "
                        "used in offices and businesses. Email clients surface priority "
                        "messages and suggest replies. Productivity suites can draft "
                        "documents and summarise meetings. Developer tools like GitHub "
                        "Copilot suggest code completions as you type. Customer relationship "
                        "management systems predict which leads are likely to convert. "
                        "AI-powered search can answer questions directly rather than "
                        "returning a list of links. Understanding the capabilities and "
                        "limitations of these tools — and recognising when their outputs "
                        "need human verification — is becoming a core professional skill "
                        "across almost every industry.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Ethics & Responsibility",
                "snippets": [
                    {
                        "title": "Bias in AI Systems",
                        "body": "AI models learn from historical data, and if that data "
                        "reflects historical inequalities, the model will perpetuate them. "
                        "Hiring algorithms trained on past recruitment data may "
                        "systematically disadvantage women if past hiring was male-dominated. "
                        "Facial recognition systems have shown higher error rates for "
                        "darker-skinned individuals when trained predominantly on "
                        "lighter-skinned faces. Bias can enter through the training data, "
                        "through flawed problem framing, or through feedback loops that "
                        "reinforce existing patterns. Addressing bias requires diverse "
                        "datasets, representative testing, and ongoing auditing of "
                        "real-world outcomes after deployment.",
                        "content_type": "article",
                    },
                    {
                        "title": "Data Privacy and Consent",
                        "body": "AI systems that profile individuals — inferring their "
                        "interests, health, or behaviour — raise significant privacy concerns. "
                        "In the UK, the UK GDPR requires that personal data is collected "
                        "lawfully, used only for the stated purpose, and retained no longer "
                        "than necessary. Individuals have the right to access data held about "
                        "them, to have it corrected, and in some cases to have it deleted. "
                        "Consent must be freely given, specific, and informed — pre-ticked "
                        "boxes do not constitute consent. For AI systems processing children's "
                        "data, the ICO Children's Code imposes additional requirements around "
                        "transparency and data minimisation.",
                        "content_type": "article",
                    },
                    {
                        "title": "Responsible AI Frameworks",
                        "body": "Organisations and governments are developing frameworks to "
                        "govern the responsible use of AI. The UK government's AI Safety "
                        "Institute focuses on evaluating risks from frontier AI models. The "
                        "EU AI Act classifies AI systems by risk level and imposes stricter "
                        "obligations on higher-risk uses such as credit scoring, biometric "
                        "surveillance, and employment decisions. Internal responsible AI "
                        "principles typically cover fairness, reliability, transparency, "
                        "privacy, and human oversight. Putting these into practice means "
                        "involving affected communities in design, documenting model "
                        "limitations, providing explanations for automated decisions, and "
                        "maintaining human accountability for outcomes.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 6. Business in the Digital Age ──────────────────────────────────────────
    {
        "title": "Business in the Digital Age",
        "description": "Explore how digital technology is transforming how businesses operate, "
        "market themselves, manage projects, and make decisions using data.",
        "icon": "briefcase",
        "t_level_topic_slug": "digital-business-services",
        "sides": [
            {
                "title": "Digital Transformation",
                "snippets": [
                    {
                        "title": "What Is Digital Transformation?",
                        "body": "Digital transformation is the process of integrating digital "
                        "technology into every area of a business, fundamentally changing how "
                        "it operates and delivers value to customers. It goes beyond simply "
                        "digitising paper processes — it involves rethinking processes, "
                        "culture, and customer experiences from the ground up. Successful "
                        "transformations require leadership commitment, a clear vision, and "
                        "willingness to challenge established ways of working. Businesses "
                        "that fail to adapt risk being outpaced by more agile competitors. "
                        "The COVID-19 pandemic accelerated digital transformation across "
                        "many sectors, compressing changes that might have taken years into "
                        "a matter of months.",
                        "content_type": "article",
                    },
                    {
                        "title": "Legacy Systems and Modernisation",
                        "body": "A legacy system is old technology that still powers critical "
                        "business operations but is expensive to maintain, difficult to "
                        "integrate with modern tools, and often impossible to scale. Many "
                        "large UK organisations — banks, government departments, NHS trusts — "
                        "rely on systems built decades ago. Modernisation strategies range "
                        "from 'lift and shift' (moving the existing system to the cloud with "
                        "minimal changes) to full rewrites in modern technology. A strangler "
                        "fig pattern gradually replaces parts of the legacy system with new "
                        "services, allowing migration without a risky big-bang cutover. "
                        "Each approach carries different costs, risks, and timelines.",
                        "content_type": "article",
                    },
                    {
                        "title": "Change Management in Tech Projects",
                        "body": "Technology projects often fail not because the technology is "
                        "wrong but because the people affected by the change were not brought "
                        "along. Change management is the discipline of planning, "
                        "communicating, and supporting the human side of change. Key "
                        "practices include involving stakeholders early to surface concerns "
                        "before they become blockers, communicating clearly about what is "
                        "changing and why, providing training before new systems go live, and "
                        "having a feedback mechanism so problems can be surfaced and resolved "
                        "quickly after launch. Resistance to change is normal and expected; "
                        "effective change management addresses the root causes of that "
                        "resistance rather than dismissing it.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "E-Commerce & Digital Marketing",
                "snippets": [
                    {
                        "title": "How Online Retail Works",
                        "body": "An e-commerce platform enables businesses to sell goods and "
                        "services over the internet. Core components include a product "
                        "catalogue and search, a shopping cart, a secure checkout and payment "
                        "processing (typically handled by a payment gateway like Stripe), "
                        "order management, and fulfilment and delivery tracking. Platforms "
                        "like Shopify, WooCommerce, and Magento provide these capabilities "
                        "out of the box. Large retailers build bespoke systems at scale. The "
                        "rise of mobile commerce means the checkout experience on a phone is "
                        "now as important as on a desktop, and checkout friction — any step "
                        "that adds unnecessary effort — directly reduces conversion rates.",
                        "content_type": "article",
                    },
                    {
                        "title": "SEO, Social Media, and Content Marketing",
                        "body": "Search engine optimisation (SEO) improves a website's "
                        "visibility in unpaid search results. It involves producing "
                        "high-quality content that matches what people search for, "
                        "structuring pages with clear headings and semantic HTML, building "
                        "links from reputable sites, and ensuring fast load times. Social "
                        "media marketing builds an audience on platforms like Instagram, "
                        "TikTok, and LinkedIn through organic content and paid advertising. "
                        "Content marketing creates useful or entertaining material — articles, "
                        "videos, podcasts — that attracts and retains an audience rather than "
                        "interrupting them with adverts. Together these form the core of "
                        "inbound marketing.",
                        "content_type": "article",
                    },
                    {
                        "title": "Analytics and Conversion Tracking",
                        "body": "Web analytics tools like Google Analytics track how visitors "
                        "find and interact with a website: where they come from, which pages "
                        "they visit, how long they stay, and where they leave. A conversion "
                        "is a desired action — a purchase, a sign-up, a contact form "
                        "submission. The conversion rate is the percentage of visitors who "
                        "complete it. Funnel analysis examines where in a multi-step process "
                        "users drop off, highlighting where the biggest improvements can be "
                        "made. Event tracking records specific interactions like button "
                        "clicks and video plays. These insights let marketing and product "
                        "teams make evidence-based decisions rather than guessing what is "
                        "working.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Agile Working",
                "snippets": [
                    {
                        "title": "Agile Principles and the Sprint Cycle",
                        "body": "Agile is an approach to project management that breaks work "
                        "into short, time-boxed iterations called sprints — usually one to "
                        "four weeks long. At the start of a sprint, the team selects a set "
                        "of features from a prioritised backlog and commits to completing "
                        "them. At the end, they demonstrate working software to stakeholders "
                        "and retrospect on how the team worked together. The Agile Manifesto "
                        "values individuals and interactions over processes and tools, working "
                        "software over comprehensive documentation, customer collaboration "
                        "over contract negotiation, and responding to change over following a "
                        "plan. Agile does not mean no planning — it means planning in shorter "
                        "cycles and adapting as you learn.",
                        "content_type": "article",
                    },
                    {
                        "title": "Scrum Roles and Ceremonies",
                        "body": "Scrum is the most widely used Agile framework. It defines "
                        "three roles: the Product Owner (responsible for the backlog and "
                        "prioritisation), the Scrum Master (facilitates the process and "
                        "removes blockers), and the Development Team (delivers the work). "
                        "Four ceremonies structure each sprint: Sprint Planning (deciding "
                        "what to build), the Daily Standup (a brief daily sync on progress "
                        "and blockers), the Sprint Review (demonstrating completed work to "
                        "stakeholders), and the Sprint Retrospective (reflecting on team "
                        "process). These ceremonies create regular feedback loops that "
                        "surface problems early and keep everyone aligned on goals.",
                        "content_type": "article",
                    },
                    {
                        "title": "Kanban and Continuous Delivery",
                        "body": "Kanban is a visual workflow management method that uses a "
                        "board with columns representing stages of work — for example, "
                        "'To Do', 'In Progress', 'Review', and 'Done'. Work items are cards "
                        "that move across the board as they progress. Unlike Scrum, Kanban "
                        "has no fixed iterations — items flow continuously. A key principle "
                        "is limiting work in progress (WIP): if too many items are being "
                        "worked on simultaneously, finishing any one of them becomes slower. "
                        "Continuous delivery extends Agile into deployment: code is "
                        "integrated and tested automatically on every change, so working "
                        "software can be released at any time rather than only at the end "
                        "of a fixed sprint.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Data-Driven Decision Making",
                "snippets": [
                    {
                        "title": "KPIs and Business Metrics",
                        "body": "A Key Performance Indicator (KPI) is a measurable value that "
                        "reflects how effectively a business or team is achieving its goals. "
                        "Good KPIs are specific, measurable, achievable, relevant, and "
                        "time-bound (SMART). Examples include monthly active users, customer "
                        "acquisition cost, net promoter score, and revenue per employee. "
                        "The challenge is choosing KPIs that genuinely reflect progress "
                        "toward real goals rather than vanity metrics — numbers that look "
                        "impressive but don't drive meaningful decisions. Tracking too many "
                        "KPIs is as unhelpful as tracking too few; a focused dashboard of "
                        "five to ten well-chosen metrics is usually more actionable.",
                        "content_type": "article",
                    },
                    {
                        "title": "Business Intelligence Tools",
                        "body": "Business intelligence (BI) tools transform raw data into "
                        "interactive dashboards and reports that non-technical users can "
                        "explore. Popular platforms include Tableau, Power BI (from "
                        "Microsoft), and Looker. They connect to databases, spreadsheets, "
                        "and cloud services, then allow users to drag and drop dimensions "
                        "and measures to build charts and filter data. A well-designed BI "
                        "dashboard gives a team a shared, real-time view of performance — "
                        "replacing slow, error-prone manual reporting. The discipline of "
                        "designing clear, honest dashboards is itself a skill: charts that "
                        "mislead or overwhelm are worse than no chart at all.",
                        "content_type": "article",
                    },
                    {
                        "title": "A/B Testing and Experimentation",
                        "body": "An A/B test compares two versions of something — a webpage, "
                        "an email subject line, a button colour — by randomly showing each "
                        "version to a different segment of users and measuring which "
                        "performs better. Because users are randomly assigned, any "
                        "difference in outcome can be attributed to the change rather than "
                        "other factors. Statistical significance testing tells us whether "
                        "an observed difference is large enough to be real or might just be "
                        "chance. A/B testing embeds a culture of evidence-based "
                        "decision-making, replacing 'I think X will work' with 'the data "
                        "shows X worked'. Large companies run hundreds of simultaneous "
                        "experiments at any given time.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 7. NHS & Healthcare Technology ──────────────────────────────────────────
    {
        "title": "NHS & Healthcare Technology",
        "description": "Discover how digital technology is transforming the NHS — from "
        "electronic patient records and telemedicine to AI-assisted diagnostics and wearable devices.",
        "icon": "heart",
        "t_level_topic_slug": "health",
        "sides": [
            {
                "title": "NHS Digital Infrastructure",
                "snippets": [
                    {
                        "title": "The NHS App and Patient Access",
                        "body": "The NHS App, launched in 2019, gives patients in England "
                        "direct digital access to a range of NHS services. Users can view "
                        "their medical record summaries, order repeat prescriptions, book "
                        "and manage GP appointments, access NHS 111 online, and receive "
                        "healthcare communications including vaccination records. The app "
                        "authenticates users against NHS login — a single identity service — "
                        "so the same credentials work across multiple NHS digital tools. "
                        "Usage grew dramatically during the COVID-19 pandemic and has "
                        "continued to rise as patients increasingly expect digital access "
                        "to services they previously had to phone or visit in person.",
                        "content_type": "article",
                    },
                    {
                        "title": "NHS Spine: The National Network",
                        "body": "NHS Spine is the central IT infrastructure that connects "
                        "GP practices, hospitals, pharmacies, and other health organisations "
                        "across England. It underpins critical services including the "
                        "Personal Demographic Service (the master record of NHS patients), "
                        "the Electronic Prescription Service, and the Summary Care Record "
                        "(a brief medical summary accessible to clinicians treating a patient "
                        "away from their usual GP). Spine processes billions of transactions "
                        "per year and must be available continuously — downtime has immediate "
                        "clinical consequences. It connects over 27,000 organisations and "
                        "is one of the largest healthcare IT systems in the world.",
                        "content_type": "article",
                    },
                    {
                        "title": "Interoperability and Data Standards",
                        "body": "Interoperability is the ability of different healthcare IT "
                        "systems to exchange and use data with each other. Poor "
                        "interoperability means clinicians cannot see records created in a "
                        "different hospital's system, forcing them to repeat tests or work "
                        "without complete information. The NHS has adopted FHIR (Fast "
                        "Healthcare Interoperability Resources), an international standard "
                        "for structuring and exchanging health data. Clinical codes like "
                        "SNOMED CT provide a shared vocabulary for diagnoses and procedures "
                        "so records mean the same thing regardless of where they were "
                        "created. Achieving true interoperability across the NHS estate "
                        "remains an ongoing national priority.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Electronic Health Records",
                "snippets": [
                    {
                        "title": "What Are Electronic Patient Records?",
                        "body": "An Electronic Patient Record (EPR) is a digital version of "
                        "the paper charts and notes traditionally kept by hospitals and GP "
                        "practices. It stores a patient's medical history, diagnoses, "
                        "medications, allergies, test results, and clinical notes in a "
                        "structured, searchable format. Well-implemented EPRs make it faster "
                        "and safer for clinicians to find information, reduce the risk of "
                        "errors from illegible handwriting, and enable audit and quality "
                        "improvement. They also support clinical decision support tools — "
                        "alerts that warn a prescriber of a dangerous drug interaction, for "
                        "example. Most NHS hospitals are now implementing or have recently "
                        "completed a move to full EPR systems.",
                        "content_type": "article",
                    },
                    {
                        "title": "Benefits and Risks of Digitising Records",
                        "body": "Electronic records offer significant advantages over paper: "
                        "they can be accessed simultaneously by multiple clinicians, are "
                        "legible, can be backed up, and can be searched and analysed at "
                        "scale. However, digitisation introduces new risks. Cybersecurity "
                        "threats are significant — the 2017 WannaCry ransomware attack "
                        "disrupted NHS services across England. Poorly designed interfaces "
                        "can slow clinicians down, contributing to burnout. Data breaches "
                        "can expose sensitive patient information. Downtime during system "
                        "failures requires fallback procedures. Any EPR implementation must "
                        "balance the genuine benefits against these risks through careful "
                        "design, thorough training, and robust resilience planning.",
                        "content_type": "article",
                    },
                    {
                        "title": "GP Systems and Hospital EPRs",
                        "body": "GP practices in England use clinical systems like SystmOne "
                        "(developed by TPP) and EMIS Web to manage patient records, "
                        "appointments, and prescriptions. These systems also feed data into "
                        "national datasets used for population health planning. Acute "
                        "hospitals use larger, more complex EPR platforms — Epic, Oracle "
                        "Health (formerly Cerner), and Nervecentre are among the most common "
                        "in the NHS. A full hospital EPR integrates patient administration, "
                        "clinical notes, orders, results, and discharge summaries into a "
                        "single system. The NHS is moving toward greater data sharing between "
                        "GP and hospital systems so clinicians can see the complete picture "
                        "regardless of care setting.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Telemedicine & Remote Care",
                "snippets": [
                    {
                        "title": "Video Consultations in the NHS",
                        "body": "A video consultation allows a patient to speak with a "
                        "clinician over a secure video call rather than attending in person. "
                        "During the COVID-19 pandemic, GP video consultations rose from "
                        "under one percent of appointments to the majority virtually "
                        "overnight. Platforms like Attend Anywhere and Accurx are used "
                        "across the NHS. Video is well suited to follow-up appointments, "
                        "mental health support, and consultations that don't require a "
                        "physical examination. It reduces travel time and cost for patients, "
                        "particularly those in rural areas or with mobility difficulties, "
                        "but is less appropriate for patients with limited internet access "
                        "or those who struggle with technology.",
                        "content_type": "article",
                    },
                    {
                        "title": "Remote Monitoring and Telehealth Devices",
                        "body": "Remote monitoring uses connected devices to collect patient "
                        "health data at home and transmit it to a clinical team. Patients "
                        "with chronic conditions like heart failure or COPD can have their "
                        "blood pressure, oxygen saturation, weight, or ECG monitored daily "
                        "without attending a clinic. If readings stray outside safe "
                        "parameters, a clinician is alerted and can intervene before the "
                        "patient deteriorates to the point of needing emergency admission. "
                        "NHS virtual wards use this model to care for patients who would "
                        "previously have required a hospital bed, freeing capacity while "
                        "keeping patients in their preferred environment at home.",
                        "content_type": "article",
                    },
                    {
                        "title": "Challenges of Digital-First Healthcare",
                        "body": "A digital-first NHS brings real benefits but also risks "
                        "excluding the people who most need support. Older patients, those "
                        "with low digital literacy, and those without a smartphone or "
                        "reliable broadband may be unable to access digital services. "
                        "Language barriers, visual or cognitive impairments, and lack of "
                        "confidence all reduce access. If digital routes replace rather than "
                        "supplement traditional ones, inequalities can widen. The NHS "
                        "digital inclusion strategy aims to address this by supporting "
                        "patients to build digital skills and ensuring non-digital routes "
                        "remain available. Designing accessible healthcare technology "
                        "requires involving diverse users throughout the design process.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Wearables & AI Diagnostics",
                "snippets": [
                    {
                        "title": "Smartwatches and Health Tracking",
                        "body": "Modern smartwatches and fitness trackers can measure heart "
                        "rate, blood oxygen saturation, sleep quality, step count, and — in "
                        "some models — electrocardiograms (ECG) and atrial fibrillation "
                        "detection. Continuous passive monitoring means that unusual patterns "
                        "can surface symptoms that a patient might not notice themselves or "
                        "that wouldn't appear in a brief clinic visit. Apple Watch's ECG "
                        "feature has been credited with detecting undiagnosed atrial "
                        "fibrillation in thousands of users. Challenges include data overload "
                        "for clinicians, the risk of anxiety from false alarms, data privacy "
                        "concerns around health data held by technology companies, and the "
                        "fact that wearables are mostly owned by younger, healthier, and "
                        "more affluent populations.",
                        "content_type": "article",
                    },
                    {
                        "title": "AI in Radiology and Pathology",
                        "body": "AI tools are being deployed to assist clinicians with "
                        "image-based diagnostics. In radiology, deep learning models can "
                        "analyse chest X-rays to flag possible lung nodules, or brain "
                        "scans to highlight areas of potential stroke damage — tasks that "
                        "previously required expert radiologists spending minutes on each "
                        "image. In pathology, AI analyses digital slides of tissue samples "
                        "to detect cancer cells. These tools are typically deployed as "
                        "assistants rather than replacements — they triage images by urgency "
                        "or highlight areas for a clinician to review. Regulatory approval "
                        "through the MHRA is required before AI diagnostic tools can be "
                        "used clinically in the UK.",
                        "content_type": "article",
                    },
                    {
                        "title": "The Future of Predictive Healthcare",
                        "body": "Predictive healthcare uses data to identify patients at "
                        "risk of deteriorating before they show obvious symptoms, enabling "
                        "early intervention. Early warning score systems in hospitals "
                        "combine routine observations — pulse, blood pressure, respiratory "
                        "rate, temperature, oxygen saturation — into a score that flags "
                        "patients requiring urgent review. Population health analytics use "
                        "large datasets to identify communities with high rates of preventable "
                        "conditions and target resources accordingly. Genomic medicine "
                        "analyses an individual's DNA to predict predisposition to certain "
                        "diseases and personalise treatment. As NHS data is linked and AI "
                        "capabilities grow, the potential for earlier, more personalised, "
                        "and preventative care continues to expand.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },

    # ── 8. Sustainable Built Environment ────────────────────────────────────────
    {
        "title": "Sustainable Built Environment",
        "description": "Explore the principles, materials, and technologies transforming "
        "construction — from passive house design and low-carbon materials to BIM and UK planning policy.",
        "icon": "building",
        "t_level_topic_slug": "design-surveying-planning",
        "sides": [
            {
                "title": "Sustainability Principles",
                "snippets": [
                    {
                        "title": "Why Sustainability Matters in Construction",
                        "body": "The built environment is responsible for approximately "
                        "40 percent of the UK's total carbon emissions — roughly split "
                        "between the energy used in operating buildings and the embodied "
                        "carbon locked into the materials and processes of construction "
                        "itself. Heating, cooling, and powering buildings accounts for a "
                        "large share of national energy demand. Meeting the UK's legally "
                        "binding net zero target by 2050 requires radical changes to both "
                        "how we design and construct new buildings and how we upgrade the "
                        "existing housing stock. Sustainability in construction is not "
                        "just an ethical consideration — it is increasingly a regulatory "
                        "and commercial requirement.",
                        "content_type": "article",
                    },
                    {
                        "title": "The UK Net Zero Target and the Built Environment",
                        "body": "The UK Climate Change Act 2008, amended in 2019, commits "
                        "the UK to reaching net zero greenhouse gas emissions by 2050. For "
                        "the built environment, this means dramatically reducing operational "
                        "carbon (the emissions from heating, lighting, and powering "
                        "buildings) by improving insulation, moving to heat pumps and "
                        "district heating, and powering buildings with renewable electricity. "
                        "It also means tackling embodied carbon — emissions released during "
                        "the manufacture, transport, and installation of building materials, "
                        "and at end of life. The Future Homes Standard sets out requirements "
                        "to deliver new homes ready for a net zero grid.",
                        "content_type": "article",
                    },
                    {
                        "title": "Lifecycle Assessment of Buildings",
                        "body": "A lifecycle assessment (LCA) quantifies the environmental "
                        "impact of a building across its entire lifespan — from raw material "
                        "extraction and manufacturing, through construction and decades of "
                        "operation, to eventual demolition and disposal or reuse. It helps "
                        "designers make informed choices: a material with lower operational "
                        "impact might have very high embodied carbon, making it a worse "
                        "overall choice than an alternative. Whole-life carbon accounting, "
                        "which captures both embodied and operational carbon, is becoming "
                        "the standard approach in sustainable design. Software tools "
                        "including One Click LCA and the EC3 calculator automate much of "
                        "the calculation.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Green Materials & Methods",
                "snippets": [
                    {
                        "title": "Low-Carbon Materials: Timber, Hemp, and CLT",
                        "body": "Traditional construction materials like concrete and steel "
                        "have high embodied carbon — producing a tonne of cement emits "
                        "approximately 0.9 tonnes of CO₂. Timber, by contrast, stores "
                        "carbon absorbed by the tree during its growth. Mass timber products "
                        "like Cross-Laminated Timber (CLT) can replace concrete in floors, "
                        "walls, and structural frames for mid-rise buildings. Hemp-lime "
                        "(hempcrete) is an emerging low-carbon wall material made from hemp "
                        "shiv mixed with lime binder — it is breathable, insulating, and "
                        "carbon-negative over its lifecycle. Using these materials reduces "
                        "embodied carbon and is increasingly specified in ambitious "
                        "low-carbon projects.",
                        "content_type": "article",
                    },
                    {
                        "title": "Passive House Design Principles",
                        "body": "The Passive House (Passivhaus) standard is a rigorous energy "
                        "performance framework that produces buildings requiring very little "
                        "energy for heating or cooling. It achieves this through five key "
                        "principles: exceptional insulation levels, high-performance "
                        "triple-glazed windows, elimination of thermal bridges (paths through "
                        "which heat escapes), airtight construction, and mechanical "
                        "ventilation with heat recovery (MVHR) to supply fresh air without "
                        "losing heat. A certified Passive House typically uses 75 to 90 "
                        "percent less heating energy than a building built to standard UK "
                        "Building Regulations. The approach is applicable to new build and, "
                        "in adapted form, to deep retrofit of existing stock.",
                        "content_type": "article",
                    },
                    {
                        "title": "Retrofitting Existing Buildings",
                        "body": "The vast majority of the buildings the UK will use in 2050 "
                        "already exist today. Upgrading the existing housing stock — "
                        "retrofitting it with better insulation, air-sealing, efficient "
                        "heating systems, and renewable generation — is therefore as "
                        "important as building new sustainable homes. Common retrofit measures "
                        "include external or internal wall insulation, loft and floor "
                        "insulation, double or triple glazing, and replacing gas boilers "
                        "with heat pumps. A whole-house retrofit plan considers the "
                        "building's fabric, ventilation, heating, and renewables together "
                        "to avoid unintended consequences — adding insulation without "
                        "improving ventilation, for example, can cause damp and mould.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Building Information Modelling",
                "snippets": [
                    {
                        "title": "What is BIM?",
                        "body": "Building Information Modelling (BIM) is a digital process "
                        "for creating and managing information about a building throughout "
                        "its lifecycle. A BIM model is more than a 3D drawing — it is a "
                        "database of structured information about every element: geometry, "
                        "materials, performance properties, installation sequence, cost, and "
                        "maintenance requirements. All disciplines — architects, structural "
                        "engineers, mechanical and electrical engineers, contractors — work "
                        "from and contribute to a shared model, reducing the information "
                        "silos that cause errors and delays on traditional projects. The "
                        "model remains useful after construction, providing facility managers "
                        "with accurate as-built information.",
                        "content_type": "article",
                    },
                    {
                        "title": "BIM Level 2 and the UK Mandate",
                        "body": "The UK government mandated BIM Level 2 on all centrally "
                        "procured public projects from 2016. BIM Level 2 requires that "
                        "each discipline works in its own federated model and exchanges "
                        "information using defined, open standards — primarily IFC "
                        "(Industry Foundation Classes) for geometry and COBie (Construction "
                        "Operations Building Information Exchange) for asset data. This "
                        "ensures models can be used across different software packages "
                        "without vendor lock-in. The mandate drove rapid adoption across "
                        "the UK construction industry, and UK expertise in BIM is now "
                        "internationally recognised. ISO 19650 provides a global framework "
                        "for information management on construction projects.",
                        "content_type": "article",
                    },
                    {
                        "title": "Clash Detection and Coordination",
                        "body": "One of BIM's most immediately valuable applications is clash "
                        "detection: automatically identifying places in the model where "
                        "elements from different disciplines conflict — where a duct from "
                        "the mechanical model passes through a structural beam, for example. "
                        "On complex buildings, thousands of clashes can be detected and "
                        "resolved in the model before construction begins, avoiding costly "
                        "on-site changes. Software like Autodesk Navisworks and Solibri is "
                        "used to federate models from different disciplines and run clash "
                        "detection reports. Coordination meetings where design teams review "
                        "and resolve clashes together are a standard part of the BIM "
                        "workflow on major projects.",
                        "content_type": "article",
                    },
                ],
            },
            {
                "title": "Planning & Regulations",
                "snippets": [
                    {
                        "title": "UK Planning Permission Process",
                        "body": "Most significant building work in England requires planning "
                        "permission from the local planning authority (LPA), usually the "
                        "district or borough council. A planning application is assessed "
                        "against the local development plan, national planning policy, and "
                        "material considerations — neighbouring amenity, heritage impact, "
                        "highways, drainage, and biodiversity. Householder applications for "
                        "extensions are simpler; full planning applications for larger "
                        "developments involve more extensive documentation and a period of "
                        "public consultation. Permitted development rights allow certain "
                        "minor works without a formal application. Decisions can be appealed "
                        "to the Planning Inspectorate if refused.",
                        "content_type": "article",
                    },
                    {
                        "title": "Building Regulations and Part L",
                        "body": "Building Regulations set minimum standards for the design "
                        "and construction of buildings in England, covering structural "
                        "safety, fire safety, drainage, ventilation, accessibility, and "
                        "energy performance. Part L specifically covers the conservation of "
                        "fuel and power, setting minimum standards for insulation, air "
                        "tightness, and heating system efficiency. The 2021 uplift to Part L "
                        "for new homes increased the minimum standard substantially, and the "
                        "forthcoming Future Homes Standard will go further still. A Building "
                        "Control inspector approves the design and carries out inspections "
                        "during construction to verify compliance. Building without "
                        "Regulations approval where required is a criminal offence.",
                        "content_type": "article",
                    },
                    {
                        "title": "Environmental Impact Assessments",
                        "body": "An Environmental Impact Assessment (EIA) is a process "
                        "required for certain types of development likely to have significant "
                        "effects on the environment — large housing schemes, industrial "
                        "facilities, and infrastructure projects typically trigger it. The "
                        "developer prepares an Environmental Statement assessing impacts on "
                        "ecology, landscape, flood risk, air quality, noise, and heritage, "
                        "along with proposed mitigation measures. The EIA process involves "
                        "screening (deciding whether an EIA is required), scoping (agreeing "
                        "what to assess), public consultation, and submission as part of the "
                        "planning application. Statutory consultees such as Natural England, "
                        "the Environment Agency, and Historic England review the assessment.",
                        "content_type": "article",
                    },
                ],
            },
        ],
    },
]


async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
        for album in ALBUMS:
            await _seed_album(session, album)
    await engine.dispose()
    print("Seed complete.")


async def _seed_topics(session: AsyncSession) -> None:
    for topic_data in TOPICS:
        t_levels = topic_data["t_levels"]
        topic_params = {k: v for k, v in topic_data.items() if k != "t_levels"}

        await session.execute(
            text("""
                INSERT INTO topics (slug, name, description, accent_colour)
                VALUES (:slug, :name, :description, :accent_colour)
                ON CONFLICT (slug) DO NOTHING
            """),
            topic_params,
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM topics WHERE slug = :slug"),
            {"slug": topic_data["slug"]},
        )
        topic_id = result.scalar_one()

        for tl in t_levels:
            result = await session.execute(
                text("SELECT 1 FROM t_levels WHERE topic_id = :topic_id AND name = :name"),
                {"topic_id": topic_id, "name": tl["name"]},
            )
            if result.scalar_one_or_none() is None:
                await session.execute(
                    text("""
                        INSERT INTO t_levels (topic_id, name, entry_requirements, how_to_apply)
                        VALUES (:topic_id, :name, :entry_requirements, :how_to_apply)
                    """),
                    {**tl, "topic_id": topic_id},
                )

    await session.commit()


async def _seed_album(session: AsyncSession, album: dict) -> None:
    result = await session.execute(
        text(
            "SELECT id FROM t_levels WHERE topic_id = (SELECT id FROM topics WHERE slug = :slug) LIMIT 1"
        ),
        {"slug": album["t_level_topic_slug"]},
    )
    t_level_id = result.scalar_one()

    result = await session.execute(
        text("SELECT id FROM topics WHERE slug = :slug"),
        {"slug": album["t_level_topic_slug"]},
    )
    topic_id = result.scalar_one()

    content_ids: dict[str, int] = {}
    for side in album["sides"]:
        for snippet in side["snippets"]:
            result = await session.execute(
                text("SELECT id FROM content WHERE title = :title"),
                {"title": snippet["title"]},
            )
            existing_content_id = result.scalar_one_or_none()

            if existing_content_id is None:
                await session.execute(
                    text("""
                        INSERT INTO content (title, body, content_type, topic_id)
                        VALUES (:title, :body, :content_type, :topic_id)
                    """),
                    {
                        "title": snippet["title"],
                        "body": snippet["body"],
                        "content_type": snippet["content_type"],
                        "topic_id": topic_id,
                    },
                )
                await session.flush()

            result = await session.execute(
                text("SELECT id FROM content WHERE title = :title"),
                {"title": snippet["title"]},
            )
            content_ids[snippet["title"]] = result.scalar_one()

    result = await session.execute(
        text("SELECT id FROM albums WHERE title = :title"),
        {"title": album["title"]},
    )
    album_id = result.scalar_one_or_none()

    if album_id is None:
        await session.execute(
            text("""
                INSERT INTO albums (title, description, icon, t_level_id)
                VALUES (:title, :description, :icon, :t_level_id)
            """),
            {
                "title": album["title"],
                "description": album["description"],
                "icon": album["icon"],
                "t_level_id": t_level_id,
            },
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM albums WHERE title = :title"),
            {"title": album["title"]},
        )
        album_id = result.scalar_one()

    # Sides/SideContent are upserted individually so re-running this script
    # against a DB that already has this Album adds newly-introduced Sides
    # and Snippets instead of silently skipping them.
    for position, side in enumerate(album["sides"]):
        result = await session.execute(
            text("SELECT id FROM sides WHERE album_id = :album_id AND title = :title"),
            {"album_id": album_id, "title": side["title"]},
        )
        side_id = result.scalar_one_or_none()

        if side_id is None:
            await session.execute(
                text("""
                    INSERT INTO sides (album_id, title, position)
                    VALUES (:album_id, :title, :position)
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            await session.flush()

            result = await session.execute(
                text("SELECT id FROM sides WHERE album_id = :album_id AND title = :title"),
                {"album_id": album_id, "title": side["title"]},
            )
            side_id = result.scalar_one()

        for snippet_position, snippet in enumerate(side["snippets"]):
            title = snippet["title"]
            result = await session.execute(
                text(
                    "SELECT 1 FROM side_content WHERE side_id = :side_id AND content_id = :content_id"
                ),
                {"side_id": side_id, "content_id": content_ids[title]},
            )
            if result.scalar_one_or_none() is None:
                await session.execute(
                    text("""
                        INSERT INTO side_content (side_id, content_id, position)
                        VALUES (:side_id, :content_id, :position)
                    """),
                    {
                        "side_id": side_id,
                        "content_id": content_ids[title],
                        "position": snippet_position,
                    },
                )

    await session.commit()


async def embed_content() -> None:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        print("SKIP_EMBEDDINGS=true, skipping embedding phase.")
        return

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            text("SELECT id, title, body FROM content WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} snippet(s)...")
        embedded = 0
        for row in rows:
            input_text = f"{row.title}\n\n{row.body or ''}"
            vec = embed_text(input_text)
            if vec is None:
                continue
            await session.execute(
                text(
                    "UPDATE content SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.utcnow(), "id": row.id},
            )
            embedded += 1
        await session.commit()
        print(f"Snippets embedded: {embedded}/{len(rows)}.")

        result = await session.execute(
            text("SELECT id, title, description FROM albums WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} album(s)...")
        embedded = 0
        for row in rows:
            input_text = f"{row.title}\n\n{row.description}"
            vec = embed_text(input_text)
            if vec is None:
                continue
            await session.execute(
                text(
                    "UPDATE albums SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.utcnow(), "id": row.id},
            )
            embedded += 1
        await session.commit()
        print(f"Albums embedded: {embedded}/{len(rows)}.")

    await engine.dispose()


if __name__ == "__main__":
    if "--embed-only" in sys.argv:
        asyncio.run(embed_content())
    else:
        asyncio.run(seed())
        asyncio.run(embed_content())
