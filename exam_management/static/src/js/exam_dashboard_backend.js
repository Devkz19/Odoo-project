/** @odoo-module **/

import AbstractAction from 'web.AbstractAction';
import { registry } from '@web/core/registry';

const ExamDashboard = AbstractAction.extend({
    template: "exam_dashboard_template",

    start: function () {
        this._super.apply(this, arguments);

        // Ensure DOM is ready before rendering chart
        setTimeout(() => {
            const ctx = this.el.querySelector("#exam_chart");
            if (ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ["Math", "Science", "History", "English"],
                        datasets: [{
                            label: "Registered Students",
                            data: [12, 19, 7, 14],
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.5)',
                                'rgba(54, 162, 235, 0.5)',
                                'rgba(255, 206, 86, 0.5)',
                                'rgba(75, 192, 192, 0.5)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { position: "top" },
                            title: { display: true, text: "Exam Registrations" }
                        }
                    }
                });
            }
        }, 200);
    }
});

registry.category("actions").add("exam_dashboard_action", ExamDashboard);
export default ExamDashboard;
