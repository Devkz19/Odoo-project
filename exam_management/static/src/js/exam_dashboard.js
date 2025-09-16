/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class ExamDashboardController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");

        onMounted(() => {
            if (this.el) {
                // Handle clicks
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
}

// Register the controller for your dashboard view
registry.category("views").add("exam_dashboard", {
    ...registry.category("views").get("form"),
    Controller: ExamDashboardController,
});
