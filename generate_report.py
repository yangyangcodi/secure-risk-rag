"""Generate a sample financial risk report PDF for testing the app."""

from fpdf import FPDF


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 64, 175)
        self.cell(0, 8, "CONFIDENTIAL - INTERNAL RISK REPORT", align="C")
        self.ln(4)
        self.set_draw_color(30, 64, 175)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150)
        self.cell(0, 6, f"Page {self.page_no()} | Apex Financial Group - Risk Intelligence Division", align="C")

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(15, 23, 42)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 8, f"  {title}", fill=True)
        self.ln(6)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def metric_row(self, label, value, status=""):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(55, 65, 81)
        self.cell(80, 7, label)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(15, 23, 42)
        self.cell(60, 7, value)
        if status:
            colors = {"HIGH": (220, 38, 38), "MEDIUM": (217, 119, 6), "LOW": (22, 163, 74), "CRITICAL": (127, 29, 29)}
            r, g, b = colors.get(status, (100, 100, 100))
            self.set_text_color(r, g, b)
            self.set_font("Helvetica", "B", 10)
            self.cell(40, 7, f"[{status}]")
        self.ln(7)


pdf = ReportPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Title block
pdf.set_font("Helvetica", "B", 18)
pdf.set_text_color(15, 23, 42)
pdf.ln(2)
pdf.cell(0, 10, "Q3 2024 Enterprise Risk Assessment Report", align="C")
pdf.ln(6)
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(100, 116, 139)
pdf.cell(0, 6, "Apex Financial Group  |  Risk Intelligence Division  |  October 15, 2024", align="C")
pdf.ln(10)

# Executive Summary
pdf.section_title("1. Executive Summary")
pdf.body_text(
    "This report presents the consolidated risk assessment for Apex Financial Group for Q3 2024 "
    "(July 1 - September 30, 2024). The quarter was marked by a significant deterioration in credit "
    "quality across the retail lending portfolio, an uptick in fraud incidents, and elevated market "
    "volatility driven by central bank policy uncertainty.\n\n"
    "Overall risk posture has been elevated from MEDIUM to HIGH following a 42% surge in detected "
    "fraud cases and a default rate that breached the internal threshold of 3.5%, reaching 4.1% by "
    "quarter-end. Immediate remediation actions are recommended in the fraud and credit risk domains."
)

# Key Risk Metrics
pdf.section_title("2. Key Risk Metrics - Q3 2024")
pdf.metric_row("Overall Risk Rating:", "HIGH", "HIGH")
pdf.metric_row("Credit Default Rate:", "4.1%  (threshold: 3.5%)", "HIGH")
pdf.metric_row("Fraud Incident Count:", "847 cases  (+42% QoQ)", "HIGH")
pdf.metric_row("Fraud Loss Amount:", "$3.2M  (+38% QoQ)", "HIGH")
pdf.metric_row("Late Payment Rate (30+ days):", "6.8%  (+1.9pp QoQ)", "MEDIUM")
pdf.metric_row("Market VaR (99%, 1-day):", "$14.7M  (limit: $18M)", "MEDIUM")
pdf.metric_row("Liquidity Coverage Ratio:", "138%  (regulatory min: 100%)", "LOW")
pdf.metric_row("Capital Adequacy Ratio:", "14.2%  (regulatory min: 8%)", "LOW")
pdf.ln(2)

# Credit Risk
pdf.section_title("3. Credit Risk")
pdf.body_text(
    "Credit risk deteriorated materially in Q3 2024. The portfolio-wide default rate rose from 2.9% "
    "in Q2 to 4.1% in Q3, breaching the internal early-warning threshold of 3.5%. This represents "
    "the highest default rate recorded since Q1 2020.\n\n"
    "Key drivers of the increase include:\n"
    "  - Retail mortgage sub-portfolio: default rate increased from 1.8% to 3.2%, driven by rising "
    "interest rate resets on variable-rate loans originated in 2021-2022.\n"
    "  - Small business lending: default rate reached 7.4%, up from 5.1% in Q2, concentrated in "
    "the food & beverage and retail sectors.\n"
    "  - Consumer unsecured loans: 90-day delinquency rate rose to 5.9%, up 2.1 percentage points "
    "quarter-over-quarter.\n\n"
    "The total non-performing loan (NPL) balance stands at $187M, representing 3.8% of total loans "
    "outstanding. Provisioning has been increased by $22M to $94M to reflect the deteriorating outlook. "
    "Stress testing indicates that a further 1pp increase in default rates would require an additional "
    "$35M in provisions, which remains within capital adequacy thresholds."
)

# Fraud Risk
pdf.section_title("4. Fraud Risk")
pdf.body_text(
    "Fraud incidents surged by 42% quarter-over-quarter, representing the most significant increase "
    "in three years. A total of 847 fraud cases were confirmed in Q3, resulting in gross losses of "
    "$3.2M before recoveries. Net losses after recoveries amounted to $1.9M.\n\n"
    "Fraud breakdown by category:\n"
    "  - Card-not-present (CNP) fraud: 412 cases, $1.4M losses (largest category, +61% QoQ)\n"
    "  - Account takeover (ATO): 198 cases, $0.9M losses (+33% QoQ)\n"
    "  - Synthetic identity fraud: 147 cases, $0.6M losses (new trend, first appearance at scale)\n"
    "  - Internal fraud: 12 cases, $0.3M losses (under investigation, 3 cases referred to law enforcement)\n"
    "  - Other: 78 cases, $0.1M losses\n\n"
    "The emergence of synthetic identity fraud is a critical concern. Fraudsters are combining real "
    "and fabricated personal information to create new identities that pass standard KYC checks. "
    "Immediate enhancement of identity verification controls is recommended. The fraud team has "
    "escalated 3 internal fraud cases to law enforcement and suspended 5 employee accounts pending "
    "investigation."
)

# Market Risk
pdf.section_title("5. Market Risk")
pdf.body_text(
    "Market risk remains within approved limits but at elevated levels. The 1-day Value-at-Risk "
    "(VaR) at 99% confidence reached $14.7M at quarter-end, compared to $11.2M in Q2 2024, "
    "against an approved limit of $18M. The increase was driven by heightened volatility in interest "
    "rate markets following Federal Reserve communications on the pace of rate normalisation.\n\n"
    "Fixed income portfolio: Duration has been reduced from 5.2 years to 4.1 years in response to "
    "rate uncertainty. Mark-to-market losses on the available-for-sale (AFS) bond portfolio totalled "
    "$8.3M for the quarter, reflected in other comprehensive income (OCI).\n\n"
    "Equity portfolio: Exposure to financial sector equities increased concentration risk. The top 5 "
    "holdings now represent 38% of the equity portfolio, up from 29% in Q2. Diversification is "
    "recommended to bring concentration below the 30% internal guideline.\n\n"
    "Foreign exchange: Net open position in EUR/USD increased to $42M following a client hedging "
    "transaction. This is within the $75M approved limit. FX VaR contribution is $2.1M."
)

# Operational Risk
pdf.section_title("6. Operational & Compliance Risk")
pdf.body_text(
    "Two significant operational risk events were recorded in Q3 2024:\n\n"
    "  1. Core banking system outage (August 14, 2024): A 4-hour outage affecting online and mobile "
    "banking services impacted approximately 84,000 customers. Root cause was a failed database "
    "patch deployment. Customer compensation costs totalled $340K. A post-incident review has been "
    "completed and patch management procedures have been revised.\n\n"
    "  2. AML screening false negative (September 3, 2024): A transaction of $2.1M was processed "
    "without triggering AML alerts due to a misconfiguration in the screening rules engine. The "
    "transaction has been retrospectively reviewed and reported to the relevant regulatory authority "
    "as a suspicious activity report (SAR). The misconfiguration has been corrected.\n\n"
    "Regulatory compliance: The group remains compliant with all capital and liquidity requirements. "
    "A regulatory examination is scheduled for Q4 2024 covering AML and sanctions compliance. "
    "Preparation activities are underway. No sanctions violations were identified in Q3."
)

# Recommendations
pdf.section_title("7. Recommendations & Action Plan")
pdf.body_text(
    "Based on the Q3 2024 risk assessment, the following immediate actions are recommended:\n\n"
    "CRITICAL PRIORITY:\n"
    "  1. Activate enhanced fraud monitoring protocols for CNP and synthetic identity fraud. "
    "Deploy additional ML-based fraud detection models by November 1, 2024.\n"
    "  2. Increase credit risk provisioning by $22M and initiate portfolio review for small business "
    "lending segment. Consider tightening underwriting criteria for new originations.\n\n"
    "HIGH PRIORITY:\n"
    "  3. Conduct full AML controls review following the screening false negative incident. "
    "Engage external auditor to validate screening rule configurations by October 31, 2024.\n"
    "  4. Reduce equity portfolio concentration - top 5 holdings to be brought below 30% of "
    "equity portfolio by year-end.\n\n"
    "MEDIUM PRIORITY:\n"
    "  5. Review variable-rate mortgage portfolio for stress scenarios assuming further 150bps "
    "rate increase. Prepare customer outreach programme for borrowers at risk of payment shock.\n"
    "  6. Enhance business continuity testing frequency from quarterly to monthly for core banking "
    "systems following August outage.\n\n"
    "These recommendations will be tracked through the Risk Committee action log and reported at "
    "the next Board Risk Committee meeting on November 12, 2024."
)

# Sign-off
pdf.ln(4)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(100, 116, 139)
pdf.multi_cell(0, 6,
    "Prepared by: Risk Intelligence Division, Apex Financial Group\n"
    "Approved by: Chief Risk Officer\n"
    "Classification: Confidential - For Internal Use Only\n"
    "Report Date: October 15, 2024"
)

output_path = "q3_2024_risk_report.pdf"
pdf.output(output_path)
print(f"Generated: {output_path}")
