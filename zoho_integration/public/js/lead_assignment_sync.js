// Intercept Frappe's assignment API calls
const original_xcall = frappe.xcall;
frappe.xcall = function(method, args) {
	const result = original_xcall.apply(this, arguments);
	
	// Check if this is an assignment call for Lead
	if (method === 'frappe.desk.form.assign_to.add' || 
		method === 'frappe.desk.form.assign_to.remove' ||
		method === 'frappe.desk.form.assign_to.close') {
		
		if (args && args.doctype === 'Lead' && args.name) {
			// Assignment changed for a Lead - sync owner immediately
			result.then(function() {
				// Get the form if it's open
				let frm = null;
				try {
					const route = frappe.get_route();
					if (route && route[0] === 'Form' && route[1] === 'Lead' && route[2] === args.name) {
						frm = cur_frm;
					}
				} catch(e) {
					// Route not available, continue
				}
				
				if (frm && frm.doc && frm.doc.name === args.name) {
					// Sync owner for the open form immediately
					setTimeout(function() {
						sync_lead_owner_immediately(frm);
					}, 200);
				} else {
					// Form not open, just update in database
					frappe.call({
						method: 'zoho_integration.lead_utils.sync_lead_owner_from_assignment',
						args: { lead_name: args.name },
						callback: function(r) {
							// Owner updated in database
						}
					});
				}
			}).catch(function(err) {
				console.error('Assignment error:', err);
			});
		}
	}
	
	return result;
};

// Sync Lead Owner when assignment changes
frappe.ui.form.on('Lead', {
	refresh: function(frm) {
		// Sync on form refresh
		if (frm.doc.name) {
			setTimeout(function() {
				sync_lead_owner_immediately(frm);
			}, 500);
		}
	},
	
	on_update: function(frm) {
		// Sync after document update
		if (frm.doc.name) {
			setTimeout(function() {
				sync_lead_owner_immediately(frm);
			}, 300);
		}
	}
});

// Function to sync lead owner immediately and save
function sync_lead_owner_immediately(frm) {
	if (!frm || !frm.doc || !frm.doc.name) return;
	
	// Get current assignment from database
	frappe.db.get_value('Lead', frm.doc.name, '_assign', (r) => {
		let assigned_users = [];
		if (r && r._assign) {
			try {
				assigned_users = JSON.parse(r._assign);
			} catch(e) {
				assigned_users = r._assign || [];
			}
		}
		
		const expected_owner = assigned_users && assigned_users.length > 0 ? assigned_users[0] : 'Administrator';
		const current_owner = frm.doc.lead_owner || 'Administrator';
		
		// Only update if different
		if (current_owner !== expected_owner) {
			// Update via server to ensure it's saved
			frappe.call({
				method: 'zoho_integration.lead_utils.sync_lead_owner_from_assignment',
				args: {
					lead_name: frm.doc.name
				},
				callback: function(response) {
					if (response.message && response.message.success) {
						const new_owner = response.message.new_owner || expected_owner;
						// Update the form field immediately
						frm.set_value('lead_owner', new_owner);
						// Force save to persist the change
						frm.save(undefined, () => {
							// Owner saved successfully
						});
					}
				},
				error: function(err) {
					console.error('Error syncing lead owner:', err);
				}
			});
		}
	});
}

