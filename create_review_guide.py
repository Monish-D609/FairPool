import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Sets internal padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_callout(doc, text, title="PRO-TIP / EXAMINER TALKING POINT"):
    """Adds a callout box for presentation talking points."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F0FDF4")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="10B981"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(f"💡 {title}: ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10.5)
    run_title.font.color.rgb = RGBColor(5, 150, 105)
    
    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(10.5)
    run_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_review_guide():
    doc = Document()
    
    # 1 inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    COLOR_PRIMARY = RGBColor(11, 19, 43)     # Deep Navy
    COLOR_SECONDARY = RGBColor(2, 132, 199)  # Electric Sky Blue
    COLOR_ACCENT = RGBColor(5, 150, 105)     # Emerald Green
    COLOR_DARK = RGBColor(30, 41, 59)        # Slate Dark
    COLOR_MUTED = RGBColor(100, 116, 139)    # Slate Muted
    
    # ==================== HEADER / TITLE ====================
    p_pre = doc.add_paragraph()
    p_pre.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_pre.add_run("VELLORE INSTITUTE OF TECHNOLOGY (VIT CHENNAI)\nSCHOOL OF COMPUTER SCIENCE AND ENGINEERING\nDESIGN AND ANALYSIS OF ALGORITHMS (DAA) — COURSE PROJECT REVIEW")
    r_inst.font.name = "Calibri"
    r_inst.font.size = Pt(11)
    r_inst.font.bold = True
    r_inst.font.color.rgb = COLOR_SECONDARY
    p_pre.paragraph_format.space_after = Pt(20)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("FairPool: Presentation & Review Defense Guide")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY
    p_title.paragraph_format.space_after = Pt(8)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Comprehensive Pitch Script, Live Demo Walkthrough, Algorithmic Defense, and Examiner Viva Q&A")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_MUTED
    p_sub.paragraph_format.space_after = Pt(28)
    
    # Quick Reference Box
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Target Review:", "Semester 5 DAA Project Review / Viva Voce Examination"),
        ("Project Scope:", "FairPool: Multi-Objective Carpool & Ride-Pooling Engine for VIT Chennai"),
        ("Sole Destination Hub:", "VIT Chennai Campus (Vandalur-Kelambakkam Main Road)"),
        ("Core DAA Pillars:", "Dijkstra Min-Heap, Shareability Graphs, Branch & Bound DFS, Set Packing ILP, Gini Detour Equity")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        cell_k = meta_tbl.cell(row_idx, 0)
        cell_v = meta_tbl.cell(row_idx, 1)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "F8FAFC")
        set_cell_background(cell_v, "FFFFFF")
        set_cell_margins(cell_k, 70, 70, 100, 100)
        set_cell_margins(cell_v, 70, 70, 100, 100)
        pk = cell_k.paragraphs[0]
        pk.paragraph_format.space_after = Pt(0)
        rk = pk.add_run(k)
        rk.font.name = "Calibri"
        rk.font.size = Pt(10)
        rk.font.bold = True
        rk.font.color.rgb = COLOR_PRIMARY
        pv = cell_v.paragraphs[0]
        pv.paragraph_format.space_after = Pt(0)
        rv = pv.add_run(v)
        rv.font.name = "Calibri"
        rv.font.size = Pt(10)
        rv.font.color.rgb = COLOR_DARK
        
    doc.add_page_break()

    # Helpers
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = COLOR_PRIMARY
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(11)
        h.paragraph_format.space_after = Pt(3)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = COLOR_SECONDARY
        return h

    def add_p(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = "Calibri"
            rb.font.size = Pt(10.5)
            rb.font.bold = True
            rb.font.color.rgb = COLOR_DARK
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        r.font.color.rgb = COLOR_DARK
        return p

    def add_script_dialogue(speaker, dialogue):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.2)
        r_spk = p.add_run(f"🗣️ {speaker}: ")
        r_spk.bold = True
        r_spk.font.name = "Calibri"
        r_spk.font.size = Pt(10.5)
        r_spk.font.color.rgb = COLOR_SECONDARY
        r_dia = p.add_run(f'"{dialogue}"')
        r_dia.italic = True
        r_dia.font.name = "Calibri"
        r_dia.font.size = Pt(10.5)
        r_dia.font.color.rgb = COLOR_DARK

    # ==================== SECTION 1 ====================
    add_h1("1. The 60-Second Opening Elevator Pitch")
    add_p(
        "Start your review with absolute confidence. Evaluators often assess 15-20 projects consecutively; a sharp, context-grounded opening immediately grabs their attention.",
        "Strategy — "
    )
    add_script_dialogue(
        "You (Presenting)",
        "Good morning, respected professors. Our DAA project is FairPool: an Algorithmic Carpooling and Ride-Pooling Optimization Platform designed specifically for our own institution, VIT Chennai, situated on the Vandalur-Kelambakkam Main Road. "
        "Every morning, thousands of students and faculty commute from residential suburbs like Tambaram, Chromepet, and OMR in single-occupancy vehicles, causing heavy bottlenecks at Vandalur and Mambakkam junctions. "
        "While standard ride-hailing algorithms maximize corporate profit, and informal carpooling fails because generous drivers suffer chronic detour burnout, FairPool solves this as a multi-objective combinatorial optimization problem: maximizing vehicle-kilometers saved while mathematically guaranteeing dynamic detour fairness across driver cohorts using the Gini coefficient. "
        "Allow us to demonstrate both the algorithmic engine and the interactive live platform."
    )
    add_callout(
        doc,
        "Notice the immediate connection to VIT Chennai's actual transit corridor. Evaluators love seeing DAA theory applied directly to solve a visible, real-world campus problem.",
        "WHY THIS WORKS"
    )

    # ==================== SECTION 2 ====================
    add_h1("2. Core Algorithmic Concepts & DAA Theoretical Defenses")
    add_p("When the panel asks 'What is the algorithmic contribution of your project?', walk through the 5-stage pipeline in order:")

    add_h2("Pillar 1: Graph Representation & Dijkstra Shortest Paths (O((|V| + |E|) log |V|))")
    add_p(
        "• Network is modeled as a weighted directed graph G = (V, E, W) where edge weights combine Haversine geodesic distance with road circuity (1.25x) and congestion speeds.\n"
        "• All-pairs shortest paths are precomputed using Dijkstra's algorithm with a min-heap priority queue into dense distance matrix D[u, v] and travel time matrix T[u, v], allowing O(1) pairwise lookups during real-time matching."
    )

    add_h2("Pillar 2: Bipartite Shareability Graph Pruning (O(|V_d| · |R|²))")
    add_p(
        "• Direct evaluation of |R| commuters across |V_d| cars would cause combinatorial explosion (O(2^|R|)).\n"
        "• We construct a Bipartite Shareability Graph G_s = (R ∪ V_d, E_s) that enforces 4 hard feasibility constraints simultaneously: (1) Earliest Departure, (2) Latest Arrival, (3) Rider Max Detour Ratio (δ_r ≤ 35%), and (4) Driver Max Detour Ceiling (Δ_v ≤ 18m).\n"
        "• Monotonicity Property: If a pair {r₁, r₂} is mutually infeasible for vehicle v, no superset containing them can be feasible, pruning >85% of candidate branches upfront."
    )

    add_h2("Pillar 3: Recursive Branch-and-Bound Permutation Enumeration")
    add_p(
        "• For each vehicle and subset of k riders (k ≤ 4 seats), we find the optimal stop sequence.\n"
        "• Strict Precedence Constraint: For every rider r, Pickup(r) MUST precede Dropoff(r). Since VIT Chennai is the sole campus destination, all drops converge at VIT Chennai.\n"
        "• Depth-First Search with early bounding terminates any branch whose travel time exceeds the driver's detour ceiling."
    )

    add_h2("Pillar 4: Multi-Objective Set Packing ILP (Integer Linear Programming)")
    add_p(
        "• Formulated as a Maximum-Weight Set Packing Problem:\n"
        "  Maximize:  ∑ Score(T) · x_T,   where Score(T) = Saved_VKM(T) - λ · Fairness_Penalty(T)\n"
        "  Subject to:  Rider exclusivity (each rider in at most 1 trip), Vehicle exclusivity (each car in at most 1 pool), and x_T ∈ {0, 1}.\n"
        "• Dual Solvers: Exact MILP branch-and-cut via SciPy HiGHS solver, and High-Speed Greedy Independent Set solver (O(|T| log |T|)) running in under 5 milliseconds."
    )

    add_h2("Pillar 5: Dynamic Fairness Ledger & Gini Disparity Optimization")
    add_p(
        "• Evaluates cumulative detour dispersion across driver cohorts using the Gini coefficient G ∈ [0, 1].\n"
        "• Over consecutive morning commute epochs, drivers who absorbed above-average detours receive an elevated penalty in subsequent set-packing runs, shifting pooling duties to rested drivers and dropping cohort Gini from 0.748 down to 0.572."
    )

    # ==================== SECTION 3 ====================
    add_h1("3. Step-by-Step Live Demonstration Script (3–5 Minutes)")
    add_p("Follow this exact sequence while sharing your screen or demonstrating on the projector:")

    add_p("1. Show the Initial Map View:", "Step 1 — ")
    add_p(
        "Point to the map: 'Here is our primary transit corridor. To eliminate visual fatigue, the default map displays exactly 6 essential pins along the Vandalur-Kelambakkam Main Road: Tambaram, Vandalur, Kandigai, VIT Chennai, Mambakkam, and Kelambakkam. Notice that VIT Chennai is highlighted in emerald green as the sole destination campus hub.'"
    )

    add_p("2. Demonstrate Dynamic 60 FPS Pin Repositioning:", "Step 2 — ")
    add_p(
        "Drag one of the suburban pins (e.g. Tambaram or Kandigai) across the map: 'All pins in our system are dynamically movable. Notice how connecting highway lines and route polylines fluidly re-anchor at 60 FPS. When released, the backend road network instantly purges its cache and updates edge lengths.'"
    )

    add_p("3. Show the Book / Offer Modal & Dynamic Point Addition:", "Step 3 — ")
    add_p(
        "Click the '+ Book / Offer' button in the top bar: 'When a commuter wants to book a ride or offer seats, they select their pickup suburb. Notice our on-demand expansion: if a student lives in Medavakkam or Siruseri, clicking it dynamically adds that new pin and its connecting highway edge directly into the active map corridor! Alternatively, clicking '+ Custom Pin' allows typing any campus landmark.'"
    )

    add_p("4. Execute Algorithmic Matching:", "Step 4 — ")
    add_p(
        "Click the green '▶ Run Match' button: 'Now the FairPool engine executes. Within milliseconds, compatible commuters are bundled into carpool trips. Notice the visual clarity:'\n"
        "  • Multi-Color Route Highlighting: Each vehicle's route is drawn in a distinct, high-contrast color (Cyan, Orange, Emerald, Violet) with a dark casing underlay so overlapping segments never blur.\n"
        "  • Vehicle Origin Badges: A floating badge (🚗 Car #1, 🚗 Car #2) marks each driver's origin.\n"
        "  • Interactive Legend: The collapsible legend lists active carpools with driver handle and commuter counts. Clicking any car highlights its specific route.\n"
        "  • Synchronized Trip Cards: On the right sidebar, each trip card features matching color borders, vehicle chips, and stop itinerary markers."
    )

    add_p("5. Showcase the Fairness Ledger & Benchmark Modal:", "Step 5 — ")
    add_p(
        "Click the Scale icon (⚖️) in the header: 'Here is our Driver Fairness Ledger. It tracks rolling detours and computes the cohort Gini disparity coefficient.'\n"
        "Next, click the Bar Chart icon (📊): 'Our benchmark tool proves that FairPool saves 35.4% of total vehicle-kilometers compared to solo driving—more than double the savings of greedy nearest-pair baselines—while preserving driver equity.'"
    )

    # ==================== SECTION 4 ====================
    add_h1("4. Expected Examiner Viva Questions & Bulletproof Model Answers")

    qas = [
        ("Q1: Is the Carpool Matching Problem NP-Hard? How do you justify it?",
         "Yes, sir/madam. Carpool trip assignment can be reduced from the Maximum-Weight Set Packing Problem, which is one of Karp's 21 classic NP-complete problems. When each trip is represented as a subset of commuters, finding a collection of pairwise disjoint subsets that maximizes total savings is equivalent to finding a maximum independent set in the trip conflict graph. To handle this, we employ a dual-solver architecture: an exact branch-and-cut MILP solver for provable bounds, and a score-density greedy heuristic running in O(|T| log |T|) for microsecond real-time responsiveness."),

        ("Q2: Why not just use Euclidean distance instead of Dijkstra?",
         "Euclidean or straight-line distance severely underestimates actual driving travel times due to Chennai's physical topography, lakes, and railway line barriers. In reality, a road route from Tambaram to VIT Chennai must navigate the Vandalur railway overbridge and arterial junctions. We use Dijkstra with a min-heap on an arterial road graph calibrated with urban circuity factor (1.25x) and realistic speed profiles, guaranteeing accurate transit estimates."),

        ("Q3: How do you enforce that a rider's pickup always happens before dropoff?",
         "In our recursive Depth-First Search trip permutation enumerator, we maintain strict state flags for each commuter. A dropoff stop for rider r is only considered a valid branching move if rider r has already been boarded at a prior pickup stop. Furthermore, since our project enforces VIT Chennai as the sole destination hub, all dropoff events naturally converge at the final destination stop (VIT Chennai), eliminating unnecessary mid-corridor detours."),

        ("Q4: What is the Gini coefficient and why is it crucial for carpooling?",
         "The Gini coefficient is a standard statistical metric of dispersion between 0 (perfect equality) and 1 (maximal inequality). In carpooling, if detour burden is concentrated on a small fraction of altruistic drivers (Gini > 0.7), those drivers quickly burn out and desert the system. FairPool penalizes candidate trips where the driver's cumulative detour exceeds the group mean. Over a 5-day cycle, this reduces driver detour Gini from 0.748 down to 0.572, sustaining long-term participation."),

        ("Q5: Why can't we just use Uber or Ola's matching algorithms?",
         "Commercial ride-hailing algorithms are designed for single on-demand pickups with dynamic surge pricing where passengers pay drivers directly. They optimize for instant corporate platform revenue rather than institutional sustainability. In a university context like VIT Chennai, commuters are peers (students and faculty), profit extraction is not the goal, and preventing driver fatigue through equitable detour rotation is the primary condition for system survival.")
    ]

    for q, a in qas:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.font.name = "Calibri"
        r_q.font.size = Pt(11)
        r_q.font.bold = True
        r_q.font.color.rgb = COLOR_PRIMARY
        
        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(6)
        p_a.paragraph_format.line_spacing = 1.15
        r_a = p_a.add_run(a)
        r_a.font.name = "Calibri"
        r_a.font.size = Pt(10.5)
        r_a.font.color.rgb = COLOR_DARK

    # ==================== SECTION 5 ====================
    add_h1("5. Algorithmic Complexity Cheat-Sheet")
    add_p("Keep this summary in mind for instant answers regarding computational bounds:")

    tbl_c = doc.add_table(rows=6, cols=4)
    tbl_c.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_heads = ["Component", "Algorithm", "Time Complexity", "Space Complexity"]
    c_rows = [
        ("Shortest Paths", "Dijkstra with Min-Heap", "O((|V| + |E|) log |V|)", "O(|V| + |E|)"),
        ("Shareability Pruning", "Pairwise Constraint Check", "O(|V_d| · |R|²)", "O(|V_d| · |R|²)"),
        ("Trip Enumerator", "Recursive DFS Branch & Bound", "O(|V_d| · (K choose C) · (2C)! / 2^C)", "O(|T|)"),
        ("Greedy Solver", "Score-Density Independent Set", "O(|T| log |T|)", "O(|T|)"),
        ("Fairness Ledger", "Cohort Gini Calculation", "O(|V_d| log |V_d|)", "O(|V_d|)")
    ]
    for col_idx, h in enumerate(c_heads):
        c = tbl_c.cell(0, col_idx)
        set_cell_background(c, "0B132B")
        set_cell_margins(c, 80, 80, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, r_data in enumerate(c_rows):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(r_data):
            c = tbl_c.cell(row_idx + 1, col_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, 70, 70, 70, 70)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif col_idx in [2, 3]:
                r.font.bold = True
                r.font.color.rgb = COLOR_SECONDARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==================== SECTION 6 ====================
    add_h1("6. High-Impact Closing Statement")
    add_script_dialogue(
        "You (Concluding)",
        "In conclusion, FairPool proves that algorithmic carpooling can achieve both high environmental efficiency and long-term commuter adoption when fairness is formulated as a first-class mathematical objective. By combining classical DAA techniques—Dijkstra shortest paths, branch-and-bound pruning, and set-packing ILP—with dynamic Gini detour balancing, FairPool delivers a mathematically sound, reproducible, and production-ready transit solution for VIT Chennai. Thank you, and we welcome your questions."
    )

    out_docx = os.path.join(os.getcwd(), "Review.docx")
    try:
        doc.save(out_docx)
        print(f"Review guide generated successfully at: {out_docx}")
    except PermissionError:
        alt_docx = os.path.join(os.getcwd(), "Review_Guide.docx")
        doc.save(alt_docx)
        print(f"Review.docx is open. Saved to: {alt_docx}")

if __name__ == "__main__":
    build_review_guide()
