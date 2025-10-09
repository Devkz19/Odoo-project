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

// Key for localStorage persistence
const LOCAL_STORAGE_USER_KEY_ID = 'pos_global_user_id';
const LOCAL_STORAGE_USER_KEY_NAME = 'pos_global_user_name';

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
        
        // Load saved user globally from localStorage
        this._loadGlobalSelectedUser();
    },
    
  
    _loadGlobalSelectedUser() {
        // 1. Check current order first (if selection was just made)
        const order = this.pos.get_order();
        if (order && order.custom_user_id) {
            this.selectedUserState.id = order.custom_user_id;
            this.selectedUserState.name = order.custom_user_name;
            return;
        }

        // 2. Load from localStorage if not found in current order
        const savedUserId = localStorage.getItem(LOCAL_STORAGE_USER_KEY_ID);
        const savedUserName = localStorage.getItem(LOCAL_STORAGE_USER_KEY_NAME);

        if (savedUserId && savedUserName) {
            this.selectedUserState.id = parseInt(savedUserId); // localStorage stores strings
            this.selectedUserState.name = savedUserName;

            // Also ensure the current order is updated with the globally selected user
            if (order) {
                order.custom_user_id = this.selectedUserState.id;
                order.custom_user_name = this.selectedUserState.name;
            }
        }
    },
    
    /**
     * Get the currently selected custom user
     */
    getSelectedUser() {
        if (this.selectedUserState.id) {
            return {
                id: this.selectedUserState.id,
                name: this.selectedUserState.name,
            };
        }
        return null;
    },

    async onClickSelector() {
        try {
            // ... (Fetching users logic remains the same) ...
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
                // Check against the state which holds the globally selected user
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
        
                localStorage.setItem(LOCAL_STORAGE_USER_KEY_ID, selectedUser.id.toString());
                localStorage.setItem(LOCAL_STORAGE_USER_KEY_NAME, selectedUser.name);
                // ---------------------------------------------
                
                console.log("Selected User:", selectedUser);
                
                // Store in current order - ensures it's attached to the order being placed
                const order = this.pos.get_order();
                if (order) {
                    order.custom_user_id = selectedUser.id;
                    order.custom_user_name = selectedUser.name;
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
     * Clear the selected user and remove from localStorage
     */
    clearSelectedUser() {
        this.selectedUserState.name = null;
        this.selectedUserState.id = null;

      
        localStorage.removeItem(LOCAL_STORAGE_USER_KEY_ID);
        localStorage.removeItem(LOCAL_STORAGE_USER_KEY_NAME);
   
        const order = this.pos.get_order();
        if (order) {
            order.custom_user_id = null;
            order.custom_user_name = null;
        }
    },
    
    /**
     * Getter method for button text
     */
    getSelectedUserName() {
        // The state (this.selectedUserState) is now correctly loaded from localStorage
        // and updated on selection/clearing, so we only need to check the state.
        if (this.selectedUserState.name) {
            return this.selectedUserState.name;
        }
        
        return _t("Select User");
    },
});