/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

// Debug: Log that the module is loading
console.log("Exam Dashboard JavaScript module is loading...");

// Dedicated function used by controller only (no inline/global triggers)
async function printDashboardToPDF() {
    console.log("printDashboardToPDF function called");
    
    const dashboardContent = document.querySelector("#exam-dashboard");
    if (!dashboardContent) {
        console.error("Dashboard content not found");
        return;
    }
    
    const printButton = document.querySelector("#dashboard-print-btn");
    if (printButton) {
        printButton.style.pointerEvents = "none";
        printButton.classList.add("disabled");
    }

    let printWindow = null;

    try {
        printWindow = window.open('', 'PRINT', 'height=900,width=1200,scrollbars=yes,resizable=yes');
        if (!printWindow) {
            console.warn('Popup blocked. Allow popups to print.');
            return;
        }

        // Wait for popup to initialize
        await new Promise(resolve => {
            if (printWindow.document && printWindow.document.readyState === 'complete') {
                resolve();
            } else {
                printWindow.addEventListener('load', resolve);
                setTimeout(resolve, 500);
            }
        });

        // Copy only stylesheets & <style> tags, not full head
        const headLinks = Array.from(document.head.querySelectorAll("link[rel='stylesheet'], style"))
            .map(node => node.outerHTML)
            .join("\n");

        const docElClass = document.documentElement.className;
        const bodyClass = document.body.className;
        const baseTag = `<base href="${location.origin + location.pathname}" />`;
        const printStyles = `
            <style>
                @page { size: A4 portrait; margin: 12mm; }
                html, body { 
                    -webkit-print-color-adjust: exact; 
                    print-color-adjust: exact;
                    margin: 0;
                    padding: 20px;
                }
                .o_form_view, .o_content { background: white !important; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
            </style>
        `;

        // Write a clean skeleton document
        printWindow.document.open();
        printWindow.document.write(`<!DOCTYPE html>
            <html class="${docElClass}">
            <head>
                ${baseTag}
                ${headLinks}
                ${printStyles}
                <meta name="viewport" content="width=device-width, initial-scale=1" />
            </head>
            <body class="${bodyClass}">
            </body>
            </html>`);
        printWindow.document.close();

        await new Promise(resolve => setTimeout(resolve, 200));

        if (!printWindow.document.body) {
            console.error("Print window document body is null");
            throw new Error("Failed to initialize print window document");
        }

        const container = printWindow.document.body;

        // Clone dashboard content
        const cloned = dashboardContent.cloneNode(true);

        // Remove the print button inside clone if any
        const btnInClone = cloned.querySelector('#dashboard-print-btn');
        if (btnInClone) btnInClone.remove();

        // Hide any interactive elements
        const interactiveElements = cloned.querySelectorAll('button, input[type="button"], .btn');
        interactiveElements.forEach(el => {
            el.style.display = 'none';
        });

        container.appendChild(cloned);

        // Match current layout width
        container.style.maxWidth = dashboardContent.offsetWidth + 'px';
        container.style.margin = '0 auto';

        // Wait for fonts, images, styles
        const whenFontsReady = printWindow.document.fonts ?
            printWindow.document.fonts.ready.catch(() => {
                console.warn("Fonts loading failed, continuing anyway");
                return Promise.resolve();
            }) : Promise.resolve();

        const whenImagesReady = new Promise((resolve) => {
            const imgs = Array.from(container.querySelectorAll('img'));
            let remaining = imgs.length;
            if (!remaining) return resolve();

            const timeout = setTimeout(() => {
                console.warn("Image loading timeout, continuing anyway");
                resolve();
            }, 3000);

            imgs.forEach((img) => {
                if (img.complete) {
                    if (--remaining === 0) {
                        clearTimeout(timeout);
                        resolve();
                    }
                } else {
                    img.addEventListener('load', () => { 
                        if (--remaining === 0) {
                            clearTimeout(timeout);
                            resolve();
                        }
                    });
                    img.addEventListener('error', () => { 
                        console.warn("Image failed to load:", img.src);
                        if (--remaining === 0) {
                            clearTimeout(timeout);
                            resolve();
                        }
                    });
                }
            });
        });

        const whenStylesReady = new Promise((resolve) => setTimeout(resolve, 500));

        await Promise.all([whenFontsReady, whenImagesReady, whenStylesReady]);

        if (printWindow.closed) {
            console.warn("Print window was closed before printing");
            return;
        }

        printWindow.focus();
        console.log(">>> About to call printWindow.print()");
        printWindow.print();

        setTimeout(() => { 
            try { 
                if (printWindow && !printWindow.closed) {
                    printWindow.close(); 
                }
            } catch (e) {
                console.warn("Error closing print window:", e);
            }
        }, 1000);

    } catch (error) {
        console.error("Error in printDashboardToPDF:", error);

        if (printWindow && !printWindow.closed) {
            try { printWindow.close(); } catch (e) {}
        }

        try { window.print(); } catch (fallbackError) {
            console.error("Fallback print also failed:", fallbackError);
        }
    } finally {
        if (printButton) {
            printButton.style.pointerEvents = "auto";
            printButton.classList.remove("disabled");
        }
    }
}

// Expose for inline handler (UI-only trigger). Guard to avoid overwriting if already present.
if (typeof window !== 'undefined' && !window.printDashboardToPDF) {
    window.printDashboardToPDF = printDashboardToPDF;
}

export class ExamDashboardController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");

        onMounted(() => {
            if (this.el) {
                console.log("Dashboard mounted, setting up event listeners");

                // Handle clicks (but exclude print button to avoid double triggers)
                this.el.addEventListener("click", this.handleDashboardClick.bind(this));

                // Attach search inputs
                const searchInputs = this.el.querySelectorAll(".dashboard-search");
                searchInputs.forEach(input => {
                    input.addEventListener("input", this.handleSearchInput.bind(this));
                });
            }
        });
    }        

    handleDashboardClick(event) {
        // Skip print button clicks (handled by inline onclick)
        if (event.target.closest("#dashboard-print-btn")) {
            return;
        }

        // Exam detail buttons
        const examButton = event.target.closest(".exam-detail-btn");
        if (examButton) {
            event.preventDefault();
            event.stopPropagation();
            const examId = examButton.dataset.examId;
            if (examId && !isNaN(examId)) {
                this.setLinkLoading(examButton, true);
                this.openRecord("exam.planning", parseInt(examId), "Exam Details")
                    .finally(() => this.setLinkLoading(examButton, false));
            } else {
                this.notification.add("Invalid exam ID", { type: "warning" });
            }
            return;
        }

        // Student profile buttons
        const studentButton = event.target.closest(".view-profile-btn");
        if (studentButton) {
            event.preventDefault();
            event.stopPropagation();
            const studentId = studentButton.dataset.studentId;
            if (studentId && !isNaN(studentId)) {
                this.setLinkLoading(studentButton, true);
                this.openRecord("student.registration", parseInt(studentId), "Student Profile")
                    .finally(() => this.setLinkLoading(studentButton, false));
            } else {
                this.notification.add("Invalid student ID", { type: "warning" });
            }
            return;
        }

        // KPI cards
        const kpiCard = event.target.closest(".kpi-card[data-action]");
        if (kpiCard) {
            event.preventDefault();
            this.handleKpiCardClick(kpiCard.dataset.action);
            return;
        }
    }

    async openRecord(model, recordId, title) {
        try {
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: title || "Record Details",
                res_model: model,
                res_id: recordId,
                views: [[false, "form"]],
                view_mode: "form",
                target: "current",
                context: this.props.context || {},
            });
        } catch (error) {
            console.error("Error opening record:", error);
            this.notification.add(`Error opening ${title}: ${error.message || "Unknown error"}`, { type: "danger" });
        }
    }

    async handleKpiCardClick(action) {
        const actionMap = {
            exams: { model: "exam.planning", name: "Exam Planning" },
            students: { model: "student.registration", name: "Student Registration" },
            halls: { model: "exam.hall", name: "Exam Halls" },
            seatings: { model: "exam.seating", name: "Exam Seating" },
        };
        const config = actionMap[action];
        if (config) {
            try {
                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: config.name,
                    res_model: config.model,
                    view_mode: "list,form",
                    views: [[false, "list"], [false, "form"]],
                    target: "current",
                });
            } catch (error) {
                console.error("Error opening list view:", error);
                this.notification.add(`Error opening ${config.name}`, { type: "danger" });
            }
        }
    }

    setLinkLoading(link, loading) {
        if (!link) return;
        if (loading) {
            link.style.pointerEvents = "none";
            link.dataset.originalText = link.innerHTML;
            link.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
            link.classList.add("disabled");
        } else {
            link.style.pointerEvents = "auto";
            if (link.dataset.originalText) {
                link.innerHTML = link.dataset.originalText;
                delete link.dataset.originalText;
            }
            link.classList.remove("disabled");
        }
    }

    handleSearchInput(event) {
        // Add search functionality here if required
    }
}

// Register the controller
console.log("Registering exam_dashboard controller...");
registry.category("views").add("exam_dashboard", {
    ...registry.category("views").get("form"),
    Controller: ExamDashboardController,
});
console.log("Exam dashboard controller registered successfully");
