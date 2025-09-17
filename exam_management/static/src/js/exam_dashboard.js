/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

// Debug: Log that the module is loading
console.log("Exam Dashboard JavaScript module is loading...");

// Debug: Add a global click handler to test if any clicks are working
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, setting up global click handler");
    
    // Add a global click handler for debugging
    document.addEventListener('click', function(event) {
        if (event.target.id === 'dashboard-print-btn' || event.target.closest('#dashboard-print-btn')) {
            console.log("GLOBAL: Print button clicked!", event);
            // Call the PDF generation function
            window.printDashboardToPDF();
        }
    });
});

// Global function for PDF generation that can be called from inline onclick
window.printDashboardToPDF = function() {
    console.log("printDashboardToPDF function called");
    
    // Check if html2pdf is available
    if (typeof html2pdf === 'undefined') {
        alert("PDF generation library not loaded. Please refresh the page.");
        console.error("html2pdf library not found");
        return;
    }
    
    // Get the dashboard content
    const dashboardContent = document.querySelector("#exam-dashboard");
    if (!dashboardContent) {
        alert("Dashboard content not found");
        console.error("Dashboard content not found");
        return;
    }
    
    console.log("Starting PDF generation...");
    
    try {
        // Show loading state
        const printButton = document.querySelector("#dashboard-print-btn");
        if (printButton) {
            printButton.style.pointerEvents = "none";
            printButton.style.opacity = "0.6";
            const originalText = printButton.innerHTML;
            printButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Generating PDF...';
        }
        
        // Create a clone of the dashboard content for printing
        const printContent = dashboardContent.cloneNode(true);
        
        // Remove the print button from the cloned content
        const clonedPrintBtn = printContent.querySelector("#dashboard-print-btn");
        if (clonedPrintBtn) {
            clonedPrintBtn.remove();
        }
        
        // Add some styling for better PDF output
        const printElement = document.createElement('div');
        printElement.style.cssText = `
            font-family: Arial, sans-serif;
            color: #333;
            background: white;
            padding: 20px;
            max-width: 100%;
        `;
        
        // Add a title for the PDF
        const titleElement = document.createElement('h1');
        titleElement.textContent = 'Exam Management Dashboard Report';
        titleElement.style.cssText = 'text-align: center; margin-bottom: 30px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;';
        printElement.appendChild(titleElement);
        
        // Add current date
        const dateElement = document.createElement('p');
        dateElement.textContent = `Generated on: ${new Date().toLocaleString()}`;
        dateElement.style.cssText = 'text-align: center; margin-bottom: 20px; color: #666; font-style: italic;';
        printElement.appendChild(dateElement);
        
        printElement.appendChild(printContent);
        
        // Configure html2pdf options
        const opt = {
            margin: [0.5, 0.5, 0.5, 0.5],
            filename: `exam_dashboard_${new Date().toISOString().split('T')[0]}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
                scale: 2,
                useCORS: true,
                letterRendering: true,
                allowTaint: true
            },
            jsPDF: { 
                unit: 'in', 
                format: 'a4', 
                orientation: 'portrait' 
            }
        };
        
        // Generate and download the PDF
        html2pdf().set(opt).from(printElement).save().then(() => {
            console.log("PDF generated successfully!");
            alert("Dashboard PDF generated successfully!");
            
            // Restore button state
            if (printButton) {
                printButton.style.pointerEvents = "auto";
                printButton.style.opacity = "1";
                printButton.innerHTML = '<i class="fa fa-print"></i> Print Dashboard';
            }
        }).catch((error) => {
            console.error("Error generating PDF:", error);
            alert(`Error generating PDF: ${error.message || "Unknown error"}`);
            
            // Restore button state
            if (printButton) {
                printButton.style.pointerEvents = "auto";
                printButton.style.opacity = "1";
                printButton.innerHTML = '<i class="fa fa-print"></i> Print Dashboard';
            }
        });
        
    } catch (error) {
        console.error("Error in PDF generation:", error);
        alert(`Error generating PDF: ${error.message || "Unknown error"}`);
        
        // Restore button state
        const printButton = document.querySelector("#dashboard-print-btn");
        if (printButton) {
            printButton.style.pointerEvents = "auto";
            printButton.style.opacity = "1";
            printButton.innerHTML = '<i class="fa fa-print"></i> Print Dashboard';
        }
    }
};

export class ExamDashboardController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");

        onMounted(() => {
            if (this.el) {
                console.log("Dashboard mounted, setting up event listeners");
                
                // Handle clicks
                this.el.addEventListener("click", this.handleDashboardClick.bind(this));

                // Attach search inputs
                const searchInputs = this.el.querySelectorAll(".dashboard-search");
                searchInputs.forEach(input => {
                    input.addEventListener("input", this.handleSearchInput.bind(this));
                });

                // Attach print button functionality with retry mechanism
                this.attachPrintButtonListener();
                
                // Also try a direct approach after a delay
                setTimeout(() => {
                    this.attachPrintButtonListener();
                }, 500);
            }
        });
    }        

    attachPrintButtonListener() {
        // Try to find the print button with retry mechanism
        const findAndAttachPrintButton = (retries = 0) => {
            const printButton = this.el.querySelector("#dashboard-print-btn");
            console.log(`Attempt ${retries + 1}: Looking for print button`, printButton);
            
            if (printButton) {
                console.log("Print button found, attaching listener");
                console.log("Button properties:", {
                    disabled: printButton.disabled,
                    style: printButton.style.cssText,
                    className: printButton.className,
                    offsetParent: printButton.offsetParent
                });
                
                // Add a simple test click handler first
                printButton.addEventListener("click", (e) => {
                    console.log("Print button clicked!", e);
                    this.notification.add("Print button clicked! Starting PDF generation...", { type: "info" });
                });
                
                // Add the main print handler
                printButton.addEventListener("click", this.handlePrintDashboard.bind(this));
                
                // Test if button is clickable
                printButton.style.pointerEvents = "auto";
                printButton.style.cursor = "pointer";
            } else if (retries < 10) {
                // Retry after a short delay if button not found
                setTimeout(() => findAndAttachPrintButton(retries + 1), 100);
            } else {
                console.warn("Print button not found after retries");
                // Try to find all buttons for debugging
                const allButtons = this.el.querySelectorAll("button");
                console.log("All buttons found:", allButtons);
            }
        };
        findAndAttachPrintButton();
    }

    handleDashboardClick(event) {
        // Handle print button clicks
        const printButton = event.target.closest("#dashboard-print-btn");
        if (printButton) {
            event.preventDefault();
            event.stopPropagation();
            this.handlePrintDashboard(event);
            return;
        }

        // Handle exam detail buttons
        const examButton = event.target.closest(".exam-detail-btn");
        if (examButton) {
            event.preventDefault();
            event.stopPropagation();

            const examId = examButton.dataset.examId;
            if (examId && !isNaN(examId)) {
                this.setLinkLoading(examButton, true);
                this.openRecord("exam.planning", parseInt(examId), "Exam Details")
                    .finally(() => {
                        this.setLinkLoading(examButton, false);
                    });
            } else {
                this.notification.add("Invalid exam ID", { type: "warning" });
            }
            return;
        }

        // Handle student profile buttons
        const studentButton = event.target.closest(".view-profile-btn");
        if (studentButton) {
            event.preventDefault();
            event.stopPropagation();

            const studentId = studentButton.dataset.studentId;
            if (studentId && !isNaN(studentId)) {
                this.setLinkLoading(studentButton, true);
                this.openRecord("student.registration", parseInt(studentId), "Student Profile")
                    .finally(() => {
                        this.setLinkLoading(studentButton, false);
                    });
            } else {
                this.notification.add("Invalid student ID", { type: "warning" });
            }
            return;
        }

        // Handle KPI card clicks
        const kpiCard = event.target.closest(".kpi-card[data-action]");
        if (kpiCard) {
            event.preventDefault();
            const action = kpiCard.dataset.action;
            this.handleKpiCardClick(action);
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
            this.notification.add(
                `Error opening ${title}: ${error.message || "Unknown error"}`,
                { type: "danger" }
            );
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
                    views: [
                        [false, "list"],
                        [false, "form"],
                    ],
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
        // Handle search input functionality if needed
        // This method is referenced but not implemented
        // Add search functionality here if required
    }

    async handlePrintDashboard(event) {
        console.log("Print dashboard function called", event);
        event.preventDefault();
        event.stopPropagation();

        const printButton = event.target.closest("#dashboard-print-btn");
        if (!printButton) {
            console.warn("Print button not found in event target");
            return;
        }

        console.log("Print button found, starting PDF generation");

        try {
            // Show loading state
            this.setLinkLoading(printButton, true);

            // Get the dashboard content
            const dashboardContent = this.el.querySelector("#exam-dashboard");
            if (!dashboardContent) {
                this.notification.add("Dashboard content not found", { type: "warning" });
                return;
            }

            // Check if html2pdf is available
            if (typeof html2pdf === 'undefined') {
                this.notification.add("PDF generation library not loaded. Please refresh the page.", { type: "error" });
                return;
            }

            // Create a clone of the dashboard content for printing
            const printContent = dashboardContent.cloneNode(true);
            
            // Remove the print button from the cloned content
            const clonedPrintBtn = printContent.querySelector("#dashboard-print-btn");
            if (clonedPrintBtn) {
                clonedPrintBtn.remove();
            }

            // Add some styling for better PDF output
            const printElement = document.createElement('div');
            printElement.style.cssText = `
                font-family: Arial, sans-serif;
                color: #333;
                background: white;
                padding: 20px;
                max-width: 100%;
            `;
            
            // Add a title for the PDF
            const titleElement = document.createElement('h1');
            titleElement.textContent = 'Exam Management Dashboard Report';
            titleElement.style.cssText = 'text-align: center; margin-bottom: 30px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;';
            printElement.appendChild(titleElement);
            
            // Add current date
            const dateElement = document.createElement('p');
            dateElement.textContent = `Generated on: ${new Date().toLocaleString()}`;
            dateElement.style.cssText = 'text-align: center; margin-bottom: 20px; color: #666; font-style: italic;';
            printElement.appendChild(dateElement);
            
            printElement.appendChild(printContent);

            // Configure html2pdf options
            const opt = {
                margin: [0.5, 0.5, 0.5, 0.5],
                filename: `exam_dashboard_${new Date().toISOString().split('T')[0]}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { 
                    scale: 2,
                    useCORS: true,
                    letterRendering: true,
                    allowTaint: true
                },
                jsPDF: { 
                    unit: 'in', 
                    format: 'a4', 
                    orientation: 'portrait' 
                }
            };

            // Generate and download the PDF
            await html2pdf().set(opt).from(printElement).save();
            
            this.notification.add("Dashboard PDF generated successfully!", { type: "success" });

        } catch (error) {
            console.error("Error generating PDF:", error);
            this.notification.add(
                `Error generating PDF: ${error.message || "Unknown error"}`,
                { type: "danger" }
            );
        } finally {
            // Remove loading state
            this.setLinkLoading(printButton, false);
        }
    }
}

// Register the controller for your dashboard view
console.log("Registering exam_dashboard controller...");
registry.category("views").add("exam_dashboard", {
    ...registry.category("views").get("form"),
    Controller: ExamDashboardController,
});
console.log("Exam dashboard controller registered successfully");
