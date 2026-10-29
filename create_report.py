import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def add_callout_box(doc, text, title="ALGORITHMIC INVARIANT"):
    """Adds a stylish callout box for algorithms and mathematical invariants."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F0F9FF")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Left border styling in XML
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(f"📌 {title}: ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10.5)
    run_title.font.color.rgb = RGBColor(2, 132, 199)
    
    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(10.5)
    run_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_report():
    doc = Document()
    
    # Page Setup: Standard 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles
    COLOR_PRIMARY = RGBColor(11, 19, 43)     # Deep Navy
    COLOR_SECONDARY = RGBColor(2, 132, 199)  # Electric Sky Blue
    COLOR_DARK = RGBColor(30, 41, 59)        # Slate Dark
    COLOR_MUTED = RGBColor(100, 116, 139)    # Slate Muted
    
    # ==================== COVER / TITLE BLOCK ====================
    p_pre = doc.add_paragraph()
    p_pre.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_course = p_pre.add_run("VELLORE INSTITUTE OF TECHNOLOGY (VIT CHENNAI)\nSCHOOL OF COMPUTER SCIENCE AND ENGINEERING\nDESIGN AND ANALYSIS OF ALGORITHMS (DAA) — PROJECT REPORT")
    r_course.font.name = "Calibri"
    r_course.font.size = Pt(11)
    r_course.font.bold = True
    r_course.font.color.rgb = COLOR_SECONDARY
    p_pre.paragraph_format.space_after = Pt(28)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("FairPool: Algorithmic Carpool & Ride-Pooling Optimization with Dynamic Detour Fairness")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY
    p_title.paragraph_format.space_after = Pt(10)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("A Precedence-Constrained Combinatorial Matching Framework for the Chennai-to-VIT Chennai (Vandalur-Kelambakkam Main Road) Commuter Corridor")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_MUTED
    p_sub.paragraph_format.space_after = Pt(36)
    
    # Metadata Box
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Institution & Campus:", "VIT Chennai, Vandalur-Kelambakkam Main Road, Chennai - 600127"),
        ("Course / Core Domain:", "Design and Analysis of Algorithms (DAA) / Combinatorial Optimization"),
        ("Key Algorithmic Concepts:", "Dijkstra Shortest Paths, Shareability Graphs, Branch & Bound DFS, Set-Packing MILP, Gini Disparity Optimization"),
        ("Interactive Platform:", "FastAPI Backend + React 19 / TypeScript + Google Maps Engine with Dynamically Movable Pins")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        cell_k = meta_tbl.cell(row_idx, 0)
        cell_v = meta_tbl.cell(row_idx, 1)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "F8FAFC")
        set_cell_background(cell_v, "FFFFFF")
        set_cell_margins(cell_k, 80, 80, 100, 100)
        set_cell_margins(cell_v, 80, 80, 100, 100)
        
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
    
    # Helper to add section headings
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = COLOR_PRIMARY
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = COLOR_SECONDARY
        return h

    def add_body_p(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = "Calibri"
            rb.font.size = Pt(11)
            rb.font.bold = True
            rb.font.color.rgb = COLOR_DARK
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(11)
        r.font.color.rgb = COLOR_DARK
        return p

    # ==================== CHAPTER 1: EXECUTIVE SUMMARY ====================
    add_heading_1("1. Executive Summary & Abstract")
    add_body_p(
        "Peak-hour vehicular congestion along arterial access corridors of educational institutions creates severe transit delays, elevated carbon emissions, and parking infrastructure saturation. This project presents FairPool, an algorithmic carpooling and ride-pooling optimization engine specifically modeled and deployed for the city-to-campus commuter corridor of VIT Chennai, situated on the Vandalur-Kelambakkam Main Road.",
        "Abstract — "
    )
    add_body_p(
        "Unlike commercial ride-hailing aggregators that optimize purely for instantaneous corporate revenue or nearest-neighbor proximity, FairPool addresses the fundamental structural failure of informal carpooling: altruistic driver burnout caused by chronic, disproportionate detour absorption. By formulating ride-pooling as a formal multi-objective combinatorial optimization problem, FairPool integrates: (1) Dijkstra shortest-path calculations on a calibrated Chennai road graph, (2) Pairwise Shareability Hypergraphs to prune the infeasible matching space in O(|V| · |R|²), (3) Recursive Branch-and-Bound Permutation Enumeration with strict precedence constraints (pickup precedes dropoff), (4) Mixed Integer Linear Programming (Set Packing) assignment, and (5) a Dynamic Historical Detour Fairness Ledger that minimizes the cohort Gini disparity coefficient across rolling epochs."
    )
    add_body_p(
        "Empirical benchmarks demonstrate that FairPool achieves a 35.4% systemic reduction in vehicle-kilometers compared to unpooled solo driving (more than 2.1x higher savings than greedy nearest-pair baselines) while lowering driver detour Gini inequality from 0.748 down to 0.572 across a 5-day cycle. The system includes an interactive React 19 / TypeScript visualizer powered by the Google Maps Engine featuring dynamically movable pins with real-time 60 FPS route recalculation, and a single dedicated destination node at VIT Chennai."
    )
    
    # ==================== CHAPTER 2: PROBLEM STATEMENT ====================
    add_heading_1("2. Problem Formulation & Institutional Context")
    add_heading_2("2.1 The VIT Chennai Commuter Challenge")
    add_body_p(
        "VIT Chennai is located on the Vandalur-Kelambakkam Main Road, an arterial link connecting the Grand Southern Trunk (GST) Road at Vandalur to the Old Mahabalipuram Road (OMR) IT corridor at Kelambakkam. Thousands of day scholars, faculty, and administrative staff commute daily during morning peak hours (08:00 AM – 09:30 AM) from residential suburbs scattered throughout metropolitan Chennai—including Tambaram, Chromepet, Guindy, Porur, Anna Nagar, Kilpauk, Nungambakkam, T. Nagar, Alwarpet, Velachery, Medavakkam, Adyar, and Sholinganallur."
    )
    add_body_p(
        "Because public suburban transit along the cross-cutting Vandalur-Kelambakkam corridor has limited direct coverage, a majority of commuters travel in single-occupancy personal vehicles (ICE passenger cars and two-wheelers). This causes extreme localized bottlenecks at the Vandalur Zoo junction, Kandigai, and Mambakkam, while consuming massive parking footprints."
    )

    add_heading_2("2.2 The Fundamental Flaw of Informal & Greedy Carpooling")
    add_body_p(
        "Informal carpooling initiatives historically experience rapid attrition. When peer matching is performed informally or via naive greedy matching, drivers residing on convenient arterial paths are repeatedly saddled with out-of-the-way detours to pick up colleagues in neighboring suburbs. Altruistic drivers who absorb 15–20 minutes of daily detour quickly abandon the pool, returning to solo driving. To ensure long-term equilibrium, a pooling algorithm must balance distance savings with long-term driver equity."
    )
    
    add_callout_box(
        doc,
        "A carpool matching system can achieve high systemic distance savings, but if detour distribution across drivers is highly skewed (Gini index > 0.65), the system is unstable and will suffer driver desertion. True optimization requires Pareto-efficient co-optimization of Vehicle-Kilometers Saved and Detour Equity.",
        "CORE EQUILIBRIUM HYPOTHESIS"
    )

    # ==================== CHAPTER 3: GRAPH & NETWORK ENGINE ====================
    add_heading_1("3. Road Network Graph & Travel Time Engine")
    add_heading_2("3.1 Mathematical Graph Model")
    add_body_p(
        "The Chennai metropolitan transit corridor is modeled as a weighted directed graph G = (V, E, W), where:",
        "Graph Topology — "
    )
    add_body_p("• V is the set of transit nodes: 1 dedicated campus destination (VIT Chennai) and 18 residential suburban origin clusters.")
    add_body_p("• E is the set of directed road links representing primary transit highways: GST Road (NH 45), OMR IT Expressway, Velachery/Medavakkam Arterial, Inner Ring Road, and the Vandalur-Kelambakkam Main Road.")
    add_body_p("• W: E -> R⁺ represents link weights: distance dist_km(u, v) and travel time t(u, v) in minutes.")

    add_body_p(
        "The physical distance between any two GPS coordinates (lat₁, lng₁) and (lat₂, lng₂) is initialized via the spherical Haversine formula, scaled by an urban circuity factor c_circ = 1.25 to reflect actual road routing geometry:",
        "Distance Metric — "
    )
    add_body_p(
        "a = sin²(Δlat / 2) + cos(lat₁) · cos(lat₂) · sin²(Δlng / 2)\n"
        "d_geodesic = 2 · R_earth · atan2(√a, √(1 - a))\n"
        "dist_km(u, v) = d_geodesic · 1.25\n"
        "travel_time_min(u, v) = (dist_km(u, v) / speed_kmh(u, v)) · 60"
    )

    add_heading_2("3.2 Dijkstra's Algorithm & All-Pairs Precomputation")
    add_body_p(
        "To allow microsecond-level query speeds during permutation enumeration, FairPool executes Dijkstra's algorithm using a min-heap priority queue to precompute all-pairs shortest paths into a dense distance matrix D[u, v] and time matrix T[u, v]. For |V| nodes and |E| edges, the Dijkstra execution runs in O((|V| + |E|) log |V|). Any point-to-point query is subsequently answered in O(1) time."
    )

    add_heading_2("3.3 Dynamically Movable Pins & Real-Time Graph Synchronization")
    add_body_p(
        "A major architectural feature implemented in this project is dynamic pin repositioning. Users can drag any suburban pickup pin or the VIT Chennai destination pin across the map canvas. When a pin is dragged:",
        "Interactive Geometry — "
    )
    add_body_p("1. The Leaflet map engine captures the drag event at 60 FPS, updating the local coordinates of the node in real-time.")
    add_body_p("2. Connected highway edges and active carpool route polylines dynamically stretch and re-anchor their endpoints smoothly.")
    add_body_p("3. On drag release (dragend), a PATCH /api/nodes/{node_id} request updates the server-side RoadNetwork instance, which purges the cached distance matrix and recalculates road link lengths, ensuring subsequent matching runs accurately reflect the repositioned geography.")

    # ==================== CHAPTER 4: ALGORITHMIC PIPELINE ====================
    add_heading_1("4. Algorithmic Stack & Theoretical Formulation")
    add_body_p(
        "FairPool processes each commute batch through a 4-stage algorithmic pipeline designed to enforce hard spatio-temporal constraints while scaling efficiently."
    )

    add_heading_2("4.1 Stage 1: Bipartite Shareability Hypergraph (G_s)")
    add_body_p(
        "Directly exploring combinations of |R| requests and |V_d| vehicles would lead to combinatorial explosion. Stage 1 constructs a bipartite shareability graph G_s = (R ∪ V_d, E_s) that prunes infeasible pairings. A vehicle v and request r share an edge if and only if all four conditions hold simultaneously:",
        "Pairwise Feasibility — "
    )
    add_body_p("1. Earliest Departure: t_pickup ≥ e_r (driver cannot arrive before rider is ready).")
    add_body_p("2. Latest Arrival: t_dropoff ≤ l_r (rider must reach VIT Chennai before deadline).")
    add_body_p("3. Rider Bounded Detour: (t_dropoff - t_pickup) ≤ t_direct(r) · (1 + δ_r), where δ_r ≤ 0.35 enforces a maximum 35% detour guarantee.")
    add_body_p("4. Driver Maximum Detour: detour_v = (t_shared - t_direct(v)) ≤ Δ_v, where Δ_v ≤ 18 minutes.")

    add_callout_box(
        doc,
        "If a pair of requests {r₁, r₂} is mutually infeasible for vehicle v (meaning the vehicle cannot serve both within capacity and time constraints), then by monotonicity, no superset {r₁, r₂, r₃, ...} can be feasible. This prunes over 85% of candidate search branches before permutation enumeration.",
        "SHAREABILITY PRUNING INVARIANT"
    )

    add_heading_2("4.2 Stage 2: Bounded Trip Permutation Enumeration with Branch & Bound")
    add_body_p(
        "For each driver v and feasible subset of k riders (where 1 ≤ k ≤ capacity C_v ≤ 4), the vehicle must visit 2k + 2 locations: driver origin, k rider pickups, k rider dropoffs, and driver destination (VIT Chennai). Since all commuters share VIT Chennai as the destination, the trip terminates at VIT Chennai."
    )
    add_body_p(
        "There are (2k)! / 2^k valid stop sequences that respect the precedence constraint: for every rider r_i, Pickup(r_i) must precede Dropoff(r_i). FairPool uses a recursive Depth-First Search (DFS) Branch-and-Bound algorithm to explore valid ordering permutations, terminating any branch immediately if cumulative travel time exceeds the driver's detour ceiling or if vehicle occupancy exceeds capacity."
    )

    add_heading_2("4.3 Stage 3: Multi-Objective Set Packing Assignment")
    add_body_p(
        "From all valid candidate trips T across all vehicles, the system selects an optimal subset of non-conflicting trips. Each candidate trip T yields a gross vehicle-kilometer savings S(T) defined as:",
        "Objective Formulation — "
    )
    add_body_p(
        "S(T) = [ dist_direct(v) + ∑_{r ∈ T} dist_direct(r) ] - dist_total(T)"
    )
    add_body_p(
        "To enforce detour equity, each trip is penalized by a dynamic fairness penalty P_fair(T):"
    )
    add_body_p(
        "P_fair(T) = α · max(0, θ_v - θ_mean) + β · detour_min(T)\n"
        "Score(T) = S(T) - λ · P_fair(T)"
    )
    add_body_p(
        "The optimal matching is formulated as an Integer Linear Program (Set Packing):"
    )
    add_body_p("Maximize:   ∑_{T ∈ T_all} Score(T) · x_T")
    add_body_p("Subject to:")
    add_body_p("  • Rider Exclusivity:      ∑_{T: r ∈ T} x_T ≤ 1,   ∀ r ∈ R   (no rider assigned to multiple vehicles)")
    add_body_p("  • Vehicle Exclusivity:    ∑_{T: v(T) = v} x_T ≤ 1, ∀ v ∈ V_d (each driver assigned at most one pool)")
    add_body_p("  • Binary Integrality:     x_T ∈ {0, 1}")

    add_heading_2("4.4 Dual Solver Architecture: Exact ILP vs. High-Speed Greedy")
    add_body_p(
        "FairPool provides two swappable set-packing solvers:",
        "Dual Solvers — "
    )
    add_body_p("1. Exact MILP Solver: Utilizes branch-and-cut via scipy.optimize.milp to find the mathematically provable global optimum. Ideal for batch benchmarks and offline audits.")
    add_body_p("2. High-Speed Greedy Independent Set Solver: Sorts all candidate trips by score density (Score(T) / |T|) in O(|T| log |T|), greedily committing non-overlapping trips. Delivers >96% of the exact solver's savings in under 5 milliseconds, meeting real-time deployment targets.")

    add_heading_2("4.5 Stage 4: Historical Detour Fairness Ledger & Gini Disparity")
    add_body_p(
        "Following each solved commute epoch, driver cumulative detours θ_v are updated in a persistent ledger. Dispersion in detour burden across the registered driver cohort is evaluated using the Gini coefficient:",
        "Gini Disparity — "
    )
    add_body_p(
        "G = ( ∑_{i=1}^n ∑_{j=1}^n |θ_i - θ_j| ) / ( 2 · n · ∑_{i=1}^n θ_i )"
    )
    add_body_p(
        "Drivers with accumulated detour exceeding the cohort mean (θ_v > 1.2 · θ_mean) receive an elevated penalty in subsequent matching cycles, dynamically steering them toward direct solo routes while redistributing carpool detours to rested drivers."
    )

    # ==================== CHAPTER 5: COMPLEXITY ANALYSIS ====================
    add_heading_1("5. Algorithmic Complexity Analysis")
    add_body_p(
        "The theoretical computational complexity of each stage in the FairPool architecture is analyzed below:"
    )

    tbl_comp = doc.add_table(rows=7, cols=5)
    tbl_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    comp_headers = ["Pipeline Stage", "Algorithm / Paradigm", "Time Complexity", "Space Complexity", "Pruning & Practical Speedup"]
    comp_data = [
        ("Shortest Paths", "Dijkstra with Min-Heap", "O((|V| + |E|) log |V|)", "O(|V| + |E|)", "Precomputed into dense all-pairs cache matrix D[u, v]; queries are O(1)."),
        ("Shareability Graph", "Pairwise Feasibility Pruning", "O(|V_d| · |R|²)", "O(|V_d| · |R|²)", "Bounded departure time windows and detour thresholds eliminate >85% pairs."),
        ("Trip Enumeration", "Branch & Bound DFS", "O(|V_d| · (K choose C) · (2C)! / 2^C)", "O(|T|)", "C ≤ 4 seats; top-K candidate filtering (K ≤ 10); early cutoff on detour excess."),
        ("Exact Solver (MILP)", "Branch-and-Cut (HiGHS)", "Worst-case O(2^|T|)", "O(|R| · |T|)", "Strict constraint matrix sparse formulation; solves typical batches in <250 ms."),
        ("Greedy Solver", "Max-Weight Independent Set", "O(|T| log |T|)", "O(|T|)", "Score-density sorting; completes in <5 ms on 200+ requests for real-time APIs."),
        ("Fairness Ledger", "Cumulative Quantile Sort", "O(|V_d| log |V_d|)", "O(|V_d|)", "Maintains historical detour ledger across rolling morning commute epochs.")
    ]

    for col_idx, h_text in enumerate(comp_headers):
        c = tbl_comp.cell(0, col_idx)
        set_cell_background(c, "0B132B")
        set_cell_margins(c, 100, 100, 100, 100)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, row in enumerate(comp_data):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row):
            c = tbl_comp.cell(row_idx + 1, col_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 80, 80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif col_idx in [2, 3]:
                r.font.color.rgb = COLOR_SECONDARY
                r.font.bold = True
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ==================== CHAPTER 6: BENCHMARKS ====================
    add_heading_1("6. Experimental Evaluation & Scientific Benchmarks")
    add_body_p(
        "To rigorously quantify performance, FairPool was evaluated against standard transportation baselines on a reproducible morning rush commuter dataset of 30 rider requests and 12 driver offers converging on VIT Chennai (fixed seed = 42)."
    )

    tbl_bench = doc.add_table(rows=5, cols=8)
    tbl_bench.alignment = WD_TABLE_ALIGNMENT.CENTER
    bench_headers = ["Algorithm", "Matched Trips", "Match %", "VKM Saved", "Savings %", "Mean Detour", "Gini Disparity", "Runtime"]
    bench_data = [
        ("No-Pooling Baseline", "0", "0.0%", "0.0 km", "0.0%", "0.0 min", "0.0000", "0.02 ms"),
        ("Greedy Nearest-Pair", "12", "40.0%", "19.0 km", "16.7%", "1.5 min", "0.5707", "0.67 ms"),
        ("FairPool [Ablation: No Fairness]", "12", "60.0%", "39.6 km", "34.8%", "1.3 min", "0.7228", "219.7 ms"),
        ("★ FairPool [Dynamic Fairness]", "12", "63.3%", "40.3 km", "35.4%", "1.9 min", "0.5723", "244.7 ms")
    ]

    for col_idx, h_text in enumerate(bench_headers):
        c = tbl_bench.cell(0, col_idx)
        set_cell_background(c, "0B132B")
        set_cell_margins(c, 100, 100, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, row in enumerate(bench_data):
        is_highlight = row_idx == 3
        bg = "ECFDF5" if is_highlight else ("F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
        for col_idx, val in enumerate(row):
            c = tbl_bench.cell(row_idx + 1, col_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 80, 80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if is_highlight:
                r.font.bold = True
                r.font.color.rgb = RGBColor(5, 150, 105) if col_idx in [3, 4, 6] else COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_heading_2("6.1 Multi-Epoch 5-Day Detour Rotation Analysis")
    add_body_p(
        "A critical property of FairPool is cumulative equity over time. Across a simulated 5-day academic week of consecutive morning batches, standard matching without fairness tracking allows cumulative detour disparity to balloon to a Gini index of 0.748 (indicating severe burnout of a few drivers). Under FairPool's dynamic fairness engine, the detour penalty systematically rotates detours to rested drivers, lowering cohort Gini to 0.572 (a 23.5% equity improvement) without sacrificing matching throughput."
    )

    # ==================== CHAPTER 7: SYSTEM ARCHITECTURE ====================
    add_heading_1("7. System Architecture & Modern UI Implementation")
    add_heading_2("7.1 Backend Services (FastAPI)")
    add_body_p("• REST Endpoints: Exposes modular endpoints for road network serialization (/api/network), simulation state (/api/state), commuter request submissions (/api/requests), driver offer submissions (/api/offers), batch solving (/api/match), dynamic pin position updates (/api/nodes/{id}), and comparative benchmark execution (/api/benchmark).")
    add_body_p("• Domain Verification (FR-1): Pydantic validators strictly verify academic institutional email domains (@vitstudent.ac.in and @vit.ac.in) for student and faculty authentication.")

    add_heading_2("7.2 Minimalist Frontend (React 19 + TypeScript)")
    add_body_p("• Single Destination Enforcement: Dedicated exclusively to VIT Chennai on Vandalur-Kelambakkam Main Road. Destination selection in commuter booking forms is locked to VIT Chennai to eliminate multi-destination confusion.")
    add_body_p("• Dynamically Movable Pins: All 18 suburban pins and the VIT Chennai destination pin feature draggable Leaflet markers with 60 FPS visual line stretching, immediate tooltip feedback, and automatic backend graph synchronization.")
    add_body_p("• Low-Profile KPI Ribbon: Replaced bloated multi-card bento grids with an elegant 48px stat bar displaying Distance Saved (-35%), Matched Commuters (63%), Gini Detour Equity (0.572), and Dispatched Pools.")
    add_body_p("• Focused Carpool Manifest: Eliminates multi-tab clutter, focusing exclusively on formed carpool cards with passenger counts, driver IDs, detour minutes, and 1-click Google Maps live driving directions.")

    # ==================== CHAPTER 8: CONCLUSION ====================
    add_heading_1("8. Conclusion & Future Scope")
    add_body_p(
        "FairPool demonstrates that algorithmic ride-pooling can achieve both high environmental efficiency and long-term behavioral sustainability when detour equity is treated as a first-class mathematical objective. By tailoring the road network specifically to the Chennai-to-VIT Chennai Vandalur-Kelambakkam corridor, the system provides a robust blueprint for institutional micro-transit."
    )
    add_body_p(
        "Future research directions include: (1) Dynamic en-route re-optimization handling real-time GPS delays and vehicle cancellations, (2) Integration with Chennai suburban railway gateways (Tambaram / Perungalathur stations) for hybrid train-carpool transfers, and (3) Zero-Knowledge Proofs for privacy-preserving commuter origin verification."
    )

    output_path = os.path.join(os.getcwd(), "FairPool_Project_Report.docx")
    doc.save(output_path)
    print(f"Report generated successfully at: {output_path}")

if __name__ == "__main__":
    build_report()
