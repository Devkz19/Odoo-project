/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        
        // Initialize state to track selected user
        this.selectedUserState = useState({
            name: null,
            id: null,
        });
        
        // Load saved user from current order (similar to partner loading)
        this._loadSelectedUser();
    },
    
    /**
     * Load the selected user from the current order
     * This ensures the selection persists across browser refreshes
     */
    _loadSelectedUser() {
        const order = this.pos.get_order();
        if (order && order.custom_user_id) {
            this.selectedUserState.id = order.custom_user_id;
            this.selectedUserState.name = order.custom_user_name;
        }
    },
    
    /**
     * Get the currently selected custom user
     * Similar to how get_partner() works
     */
    getSelectedUser() {
        const order = this.pos.get_order();
        if (order && order.custom_user_id) {
            return {
                id: order.custom_user_id,
                name: order.custom_user_name,
            };
        }
        return null;
    },

    async onClickSelector() {
        try {
            // Fetch all users using ORM service
            const users = await this.orm.searchRead(
                "res.users",
                [],
                ["name", "login"],
                { limit: 100 }
            );

            if (!users || users.length === 0) {
                this.dialog.add(AlertDialog, {
                    title: _t("No Users"),
                    body: _t("No users found in the system."),
                });
                return;
            }

            const currentUser = this.getSelectedUser();

            // Format users for the selection popup with current selection marked
            const userList = users.map(user => ({
                id: user.id,
                label: user.name,
                item: user,
                isSelected: currentUser ? user.id === currentUser.id : false,
            }));

            // Show selection popup using makeAwaitable
            const selectedUser = await makeAwaitable(this.dialog, SelectionPopup, {
                title: _t("Select User"),
                list: userList,
            });

            if (selectedUser) {
                // Update the button state with selected user
                this.selectedUserState.name = selectedUser.name;
                this.selectedUserState.id = selectedUser.id;
                
                console.log("Selected User:", selectedUser);
                
                // Store in current order - this ensures persistence
                const order = this.pos.get_order();
                if (order) {
                    // Use order.update() to ensure proper serialization and persistence
                    order.custom_user_id = selectedUser.id;
                    order.custom_user_name = selectedUser.name;
                    
                    // Alternatively, you can use the update method if your order model supports it
                    // order.update({
                    //     custom_user_id: selectedUser.id,
                    //     custom_user_name: selectedUser.name,
                    // });
                }
            }
        } catch (error) {
            console.error("Error in onClickSelector:", error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Error loading users: %s", error.message),
            });
        }
    },
    
    /**
     * Clear the selected user
     * Similar to how customer can be cleared
     */
    clearSelectedUser() {
        this.selectedUserState.name = null;
        this.selectedUserState.id = null;
        
        const order = this.pos.get_order();
        if (order) {
            order.custom_user_id = null;
            order.custom_user_name = null;
        }
    },
    
    /**
     * Getter method for button text
     * Returns the selected user name or placeholder text
     */
    getSelectedUserName() {
        // First check the state
        if (this.selectedUserState.name) {
            return this.selectedUserState.name;
        }
        
        // Then check the order (for persistence)
        const user = this.getSelectedUser();
        if (user) {
            return user.name;
        }
        
        return _t("Select User");
    },
});

