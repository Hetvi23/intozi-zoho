# Copyright (c) 2025, jignesh@nesscale.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class IntoziCRMRule(Document):
	def validate(self):
		"""Create or update Assignment Rules for Lead when Intozi CRM Rule is saved"""
		self.sync_assignment_rules()

	def sync_assignment_rules(self):
		"""
		Synchronize Frappe Assignment Rules for Lead based on Intozi CRM Rule configuration.
		Creates or updates separate Assignment Rules for each Lead Source with:
		- Document Type: Lead
		- Rule: Round Robin
		- Assignment Days: All days (Monday to Sunday)
		- Users: From assignment_rules child table grouped by lead source
		"""
		
		# Get old document to compare what lead sources existed before
		old_lead_sources = set()
		if not self.is_new():
			old_doc = frappe.get_doc("Intozi CRM Rule", self.name)
			for rule in old_doc.assignment_rules:
				if rule.lead_source:
					old_lead_sources.add(rule.lead_source)
		
		# Group current rules by lead source
		lead_source_map = {}
		for rule in self.assignment_rules:
			if rule.lead_source and rule.user:
				if rule.lead_source not in lead_source_map:
					lead_source_map[rule.lead_source] = []
				lead_source_map[rule.lead_source].append(rule.user)
		

		current_lead_sources = set(lead_source_map.keys())
		# Find lead sources that were deleted
		deleted_lead_sources = old_lead_sources - current_lead_sources
		
		created_rules = []
		updated_rules = []
		deleted_rules = []
		
		# Create or update assignment rule for each lead source
		for lead_source, users in lead_source_map.items():
			rule_name = f"Intozi CRM - {lead_source}"
			
			# Check if the assignment rule already exists
			is_existing = frappe.db.exists("Assignment Rule", rule_name)
			if is_existing:
				assignment_rule = frappe.get_doc("Assignment Rule", rule_name)
			else:
				# Create new assignment rule
				assignment_rule = frappe.new_doc("Assignment Rule")
				assignment_rule.name = rule_name
			
			# Set basic fields
			assignment_rule.document_type = "Lead"
			assignment_rule.description = f"Auto-assignment of Leads from {lead_source}"
			assignment_rule.assign_condition = f'source == "{lead_source}"'
			assignment_rule.rule = "Round Robin"
			assignment_rule.disabled = 0
			assignment_rule.priority = 0
			
			# Clear existing assignment days and add all days
			assignment_rule.assignment_days = []
			days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
			for day in days:
				assignment_rule.append("assignment_days", {"day": day})
			
			# Clear existing users and add unique users for this lead source
			assignment_rule.users = []
			unique_users = list(set(users))  # Remove duplicates
			for user in unique_users:
				assignment_rule.append("users", {"user": user})
			
			# Save the assignment rule
			assignment_rule.save(ignore_permissions=True)
			
			if is_existing:
				updated_rules.append(rule_name)
			else:
				created_rules.append(rule_name)
		
		# Delete assignment rules for lead sources that were removed
		for lead_source in deleted_lead_sources:
			rule_name = f"Intozi CRM - {lead_source}"
			try:
				if frappe.db.exists("Assignment Rule", rule_name):
					frappe.delete_doc("Assignment Rule", rule_name, ignore_permissions=True, force=True)
					deleted_rules.append(rule_name)
			except Exception as e:
				frappe.log_error(
					message=f"Failed to delete Assignment Rule {rule_name}: {str(e)}",
					title="Intozi CRM Rule - Assignment Rule Deletion Failed"
				)
		
		# Show summary message
		messages = []
		if created_rules:
			messages.append(_("{0} Assignment Rule(s) created").format(len(created_rules)))
		if updated_rules:
			messages.append(_("{0} Assignment Rule(s) updated").format(len(updated_rules)))
		if deleted_rules:
			messages.append(_("{0} Assignment Rule(s) deleted").format(len(deleted_rules)))
		
		if messages:
			frappe.msgprint(
				", ".join(messages),
				alert=True,
				indicator="green"
			)
