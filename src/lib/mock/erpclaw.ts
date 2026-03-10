import type { VerticalLayout } from '$lib/types';

export const erpclaw: VerticalLayout = {
	name: 'erpclaw',
	label: 'ERPClaw',
	description: 'Core ERP — Sales, Purchasing, Accounting, Inventory',
	icon: '📊',
	color: '#06b6d4',

	kpis: [
		{ label: 'Revenue (MTD)', value: '$142,800', sub: '+12% vs last month', color: '#10b981' },
		{ label: 'Open Invoices', value: '23', sub: '$48,200 outstanding', color: '#06b6d4' },
		{ label: 'Overdue', value: '5', sub: '$12,400 past due', color: '#ef4444' },
		{ label: 'Orders This Week', value: '18', sub: '7 pending delivery', color: '#f59e0b' }
	],

	workflows: [
		{
			key: 'order_to_cash',
			label: 'Order to Cash',
			icon: '💰',
			primaryAction: '+ New Quote',
			steps: [
				{ label: 'Quote', count: 4, countColor: '#06b6d4' },
				{ label: 'Order', count: 7, countColor: '#f59e0b' },
				{ label: 'Deliver', count: 2, countColor: '#818cf8' },
				{ label: 'Invoice', count: 3, countColor: '#10b981' },
				{ label: 'Payment' }
			]
		},
		{
			key: 'procure_to_pay',
			label: 'Procure to Pay',
			icon: '📦',
			primaryAction: '+ New PO',
			steps: [
				{ label: 'PO', count: 2, countColor: '#06b6d4' },
				{ label: 'Receipt', count: 1, countColor: '#f59e0b' },
				{ label: 'Invoice' },
				{ label: 'Payment' }
			]
		}
	],

	sidebar: [
		{
			label: 'Sales',
			icon: '🛒',
			expanded: true,
			items: [
				{ key: 'customer', label: 'Customer', labelPlural: 'Customers' },
				{ key: 'quotation', label: 'Quotation', labelPlural: 'Quotations' },
				{ key: 'sales_order', label: 'Sales Order', labelPlural: 'Sales Orders' },
				{ key: 'delivery_note', label: 'Delivery Note', labelPlural: 'Delivery Notes' },
				{ key: 'sales_invoice', label: 'Invoice', labelPlural: 'Invoices' },
				{ key: 'credit_note', label: 'Credit Note', labelPlural: 'Credit Notes' }
			]
		},
		{
			label: 'Purchasing',
			icon: '🚚',
			expanded: false,
			items: [
				{ key: 'supplier', label: 'Supplier', labelPlural: 'Suppliers' },
				{ key: 'purchase_order', label: 'Purchase Order', labelPlural: 'Purchase Orders' },
				{ key: 'purchase_receipt', label: 'Receipt', labelPlural: 'Receipts' },
				{ key: 'purchase_invoice', label: 'Vendor Invoice', labelPlural: 'Vendor Invoices' }
			]
		},
		{
			label: 'Inventory',
			icon: '📦',
			expanded: false,
			items: [
				{ key: 'item', label: 'Item', labelPlural: 'Items' },
				{ key: 'warehouse', label: 'Warehouse', labelPlural: 'Warehouses' },
				{ key: 'stock_entry', label: 'Stock Entry', labelPlural: 'Stock Entries' }
			]
		},
		{
			label: 'Accounting',
			icon: '📒',
			expanded: false,
			items: [
				{ key: 'account', label: 'Account', labelPlural: 'Chart of Accounts' },
				{ key: 'journal_entry', label: 'Journal Entry', labelPlural: 'Journal Entries' },
				{ key: 'payment_entry', label: 'Payment', labelPlural: 'Payments' }
			]
		},
		{
			label: 'HR',
			icon: '👥',
			expanded: false,
			items: [
				{ key: 'employee', label: 'Employee', labelPlural: 'Employees' },
				{ key: 'expense_claim', label: 'Expense Claim', labelPlural: 'Expense Claims' }
			]
		},
		{
			label: 'Setup',
			icon: '⚙️',
			expanded: false,
			items: [
				{ key: 'company', label: 'Company', labelPlural: 'Companies' },
				{ key: 'fiscal_year', label: 'Fiscal Year', labelPlural: 'Fiscal Years' },
				{ key: 'tax_template', label: 'Tax Template', labelPlural: 'Tax Templates' }
			]
		}
	],

	entities: {
		customer: {
			label: 'Customer',
			labelPlural: 'Customers',
			columns: [
				{ field: 'name', label: 'Name', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'territory', label: 'Territory' },
				{ field: 'email', label: 'Email' },
				{ field: 'balance', label: 'Balance', format: 'currency', align: 'right' }
			],
			filters: ['Individual', 'Company'],
			filterField: 'type',
			createForm: {
				action: 'add-customer',
				submitLabel: 'Create Customer',
				sections: [
					{
						label: 'Customer Information',
						fields: [
							{ name: 'name', label: 'Customer Name', type: 'text', required: true },
							{
								name: 'type',
								label: 'Type',
								type: 'select',
								options: ['Individual', 'Company'],
								required: true
							},
							{ name: 'territory', label: 'Territory', type: 'text' },
							{ name: 'industry', label: 'Industry', type: 'text' }
						]
					},
					{
						label: 'Contact',
						fields: [
							{ name: 'phone', label: 'Phone', type: 'tel' },
							{ name: 'email', label: 'Email', type: 'email' }
						]
					}
				]
			}
		},
		quotation: {
			label: 'Quotation',
			labelPlural: 'Quotations',
			columns: [
				{ field: 'id', label: 'ID', width: 120 },
				{ field: 'customer', label: 'Customer', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'validUntil', label: 'Valid Until', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Converted', 'Expired'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#06b6d4',
				Converted: '#10b981',
				Expired: '#ef4444'
			},
			createForm: {
				action: 'add-quotation',
				submitLabel: 'Create Quotation',
				sections: [
					{
						label: 'Quotation Details',
						fields: [
							{ name: 'customer', label: 'Customer', type: 'text', required: true },
							{ name: 'date', label: 'Date', type: 'date', required: true },
							{ name: 'valid_until', label: 'Valid Until', type: 'date' }
						]
					},
					{
						label: 'Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true },
							{ name: 'rate', label: 'Rate', type: 'currency', required: true }
						]
					}
				]
			},
			actions: ['submit-quotation', 'convert-quotation-to-so']
		},
		sales_order: {
			label: 'Sales Order',
			labelPlural: 'Sales Orders',
			columns: [
				{ field: 'id', label: 'SO#', width: 120 },
				{ field: 'customer', label: 'Customer', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'deliveryDate', label: 'Delivery Date', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Delivered', 'Cancelled'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#06b6d4',
				Delivered: '#10b981',
				Cancelled: '#ef4444',
				confirmed: '#06b6d4',
				active: '#10b981',
				draft: '#64748b',
				cancelled: '#ef4444'
			},
			createForm: {
				action: 'add-sales-order',
				submitLabel: 'Create Sales Order',
				sections: [
					{
						label: 'Order Details',
						fields: [
							{ name: 'customer', label: 'Customer', type: 'text', required: true },
							{ name: 'date', label: 'Order Date', type: 'date', required: true },
							{ name: 'delivery_date', label: 'Delivery Date', type: 'date' }
						]
					},
					{
						label: 'Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true },
							{ name: 'rate', label: 'Rate', type: 'currency', required: true },
							{ name: 'warehouse', label: 'Warehouse', type: 'text' }
						]
					}
				]
			},
			actions: ['submit-sales-order', 'create-delivery-note', 'create-sales-invoice']
		},
		delivery_note: {
			label: 'Delivery Note',
			labelPlural: 'Delivery Notes',
			columns: [
				{ field: 'id', label: 'DN#', width: 120 },
				{ field: 'customer', label: 'Customer', primary: true },
				{ field: 'salesOrder', label: 'Sales Order' },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Cancelled'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981',
				Cancelled: '#ef4444'
			},
			createForm: {
				action: 'create-delivery-note',
				submitLabel: 'Create Delivery Note',
				sections: [
					{
						label: 'Delivery Details',
						fields: [
							{ name: 'customer', label: 'Customer', type: 'text', required: true },
							{ name: 'sales_order_id', label: 'Sales Order', type: 'text', required: true },
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'warehouse', label: 'Source Warehouse', type: 'text', required: true }
						]
					}
				]
			},
			actions: ['submit-delivery-note', 'create-sales-invoice']
		},
		sales_invoice: {
			label: 'Invoice',
			labelPlural: 'Invoices',
			columns: [
				{ field: 'id', label: 'ID', width: 120 },
				{ field: 'customer', label: 'Customer', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'outstanding', label: 'Outstanding', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Paid', 'Overdue'],
			statusColors: {
				Paid: '#10b981',
				Submitted: '#06b6d4',
				Overdue: '#ef4444',
				Draft: '#64748b',
				submitted: '#06b6d4',
				draft: '#64748b',
				paid: '#10b981',
				overdue: '#ef4444'
			},
			createForm: {
				action: 'create-sales-invoice',
				submitLabel: 'Create Invoice',
				sections: [
					{
						label: 'Invoice Details',
						fields: [
							{ name: 'customer', label: 'Customer', type: 'text', required: true },
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'due_date', label: 'Due Date', type: 'date' }
						]
					},
					{
						label: 'Line Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true },
							{ name: 'rate', label: 'Rate', type: 'currency', required: true }
						]
					}
				]
			},
			actions: ['submit-sales-invoice', 'create-credit-note']
		},
		credit_note: {
			label: 'Credit Note',
			labelPlural: 'Credit Notes',
			columns: [
				{ field: 'id', label: 'CN#', width: 120 },
				{ field: 'customer', label: 'Customer', primary: true },
				{ field: 'invoice', label: 'Against Invoice' },
				{ field: 'amount', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981'
			},
			createForm: {
				action: 'create-credit-note',
				submitLabel: 'Create Credit Note',
				sections: [
					{
						label: 'Credit Note Details',
						fields: [
							{ name: 'invoice_id', label: 'Against Invoice', type: 'text', required: true },
							{ name: 'reason', label: 'Reason', type: 'textarea', required: true },
							{ name: 'amount', label: 'Amount', type: 'currency', required: true }
						]
					}
				]
			}
		},
		supplier: {
			label: 'Supplier',
			labelPlural: 'Suppliers',
			columns: [
				{ field: 'name', label: 'Name', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'territory', label: 'Territory' },
				{ field: 'balance', label: 'Balance', format: 'currency', align: 'right' }
			],
			filters: ['Individual', 'Company'],
			filterField: 'type',
			createForm: {
				action: 'add-supplier',
				submitLabel: 'Create Supplier',
				sections: [
					{
						label: 'Supplier Information',
						fields: [
							{ name: 'name', label: 'Supplier Name', type: 'text', required: true },
							{
								name: 'type',
								label: 'Type',
								type: 'select',
								options: ['Individual', 'Company'],
								required: true
							},
							{ name: 'territory', label: 'Territory', type: 'text' }
						]
					},
					{
						label: 'Contact',
						fields: [
							{ name: 'phone', label: 'Phone', type: 'tel' },
							{ name: 'email', label: 'Email', type: 'email' }
						]
					}
				]
			}
		},
		purchase_order: {
			label: 'Purchase Order',
			labelPlural: 'Purchase Orders',
			columns: [
				{ field: 'id', label: 'PO#', width: 120 },
				{ field: 'supplier', label: 'Supplier', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Received', 'Cancelled'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#06b6d4',
				Received: '#10b981',
				Cancelled: '#ef4444',
				confirmed: '#06b6d4',
				fully_invoiced: '#10b981',
				draft: '#64748b',
				cancelled: '#ef4444'
			},
			createForm: {
				action: 'add-purchase-order',
				submitLabel: 'Create Purchase Order',
				sections: [
					{
						label: 'PO Details',
						fields: [
							{ name: 'supplier', label: 'Supplier', type: 'text', required: true },
							{ name: 'date', label: 'Order Date', type: 'date', required: true },
							{ name: 'delivery_date', label: 'Expected Date', type: 'date' }
						]
					},
					{
						label: 'Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true },
							{ name: 'rate', label: 'Rate', type: 'currency', required: true }
						]
					}
				]
			},
			actions: ['submit-purchase-order', 'create-purchase-receipt']
		},
		purchase_receipt: {
			label: 'Receipt',
			labelPlural: 'Receipts',
			columns: [
				{ field: 'id', label: 'GRN#', width: 120 },
				{ field: 'supplier', label: 'Supplier', primary: true },
				{ field: 'purchaseOrder', label: 'PO#' },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981'
			},
			createForm: {
				action: 'create-purchase-receipt',
				submitLabel: 'Create Receipt',
				sections: [
					{
						label: 'Receipt Details',
						fields: [
							{ name: 'supplier', label: 'Supplier', type: 'text', required: true },
							{ name: 'purchase_order_id', label: 'Purchase Order', type: 'text', required: true },
							{ name: 'date', label: 'Receipt Date', type: 'date', required: true },
							{ name: 'warehouse', label: 'Target Warehouse', type: 'text', required: true }
						]
					}
				]
			}
		},
		purchase_invoice: {
			label: 'Vendor Invoice',
			labelPlural: 'Vendor Invoices',
			columns: [
				{ field: 'id', label: 'Bill#', width: 120 },
				{ field: 'supplier', label: 'Supplier', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'outstanding', label: 'Outstanding', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Paid', 'Overdue'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#06b6d4',
				Paid: '#10b981',
				Overdue: '#ef4444'
			},
			createForm: {
				action: 'create-purchase-invoice',
				submitLabel: 'Create Vendor Invoice',
				sections: [
					{
						label: 'Invoice Details',
						fields: [
							{ name: 'supplier', label: 'Supplier', type: 'text', required: true },
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'due_date', label: 'Due Date', type: 'date' },
							{ name: 'bill_no', label: 'Vendor Bill No.', type: 'text' }
						]
					},
					{
						label: 'Line Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true },
							{ name: 'rate', label: 'Rate', type: 'currency', required: true }
						]
					}
				]
			}
		},
		item: {
			label: 'Item',
			labelPlural: 'Items',
			columns: [
				{ field: 'name', label: 'Item Name', primary: true },
				{ field: 'group', label: 'Group' },
				{ field: 'uom', label: 'UOM' },
				{ field: 'cost', label: 'Standard Cost', format: 'currency', align: 'right' },
				{ field: 'stock', label: 'In Stock', align: 'right' }
			],
			filters: [],
			createForm: {
				action: 'add-item',
				submitLabel: 'Create Item',
				sections: [
					{
						label: 'Item Details',
						fields: [
							{ name: 'name', label: 'Item Name', type: 'text', required: true },
							{ name: 'item_group', label: 'Item Group', type: 'text' },
							{ name: 'uom', label: 'Default UOM', type: 'text', required: true },
							{ name: 'standard_cost', label: 'Standard Cost', type: 'currency' },
							{ name: 'opening_stock', label: 'Opening Stock', type: 'number' }
						]
					}
				]
			}
		},
		warehouse: {
			label: 'Warehouse',
			labelPlural: 'Warehouses',
			columns: [
				{ field: 'name', label: 'Warehouse', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'address', label: 'Address' },
				{ field: 'items', label: 'Items', align: 'right' }
			],
			filters: [],
			createForm: {
				action: 'add-warehouse',
				submitLabel: 'Create Warehouse',
				sections: [
					{
						label: 'Warehouse Details',
						fields: [
							{ name: 'name', label: 'Warehouse Name', type: 'text', required: true },
							{
								name: 'type',
								label: 'Type',
								type: 'select',
								options: ['Main', 'Transit', 'Scrap']
							},
							{ name: 'address', label: 'Address', type: 'text' }
						]
					}
				]
			}
		},
		stock_entry: {
			label: 'Stock Entry',
			labelPlural: 'Stock Entries',
			columns: [
				{ field: 'id', label: 'SE#', width: 120 },
				{ field: 'type', label: 'Type', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'from', label: 'From' },
				{ field: 'to', label: 'To' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Cancelled'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981',
				Cancelled: '#ef4444'
			},
			createForm: {
				action: 'add-stock-entry',
				submitLabel: 'Create Stock Entry',
				sections: [
					{
						label: 'Entry Details',
						fields: [
							{
								name: 'type',
								label: 'Purpose',
								type: 'select',
								options: ['Material Receipt', 'Material Transfer', 'Material Issue'],
								required: true
							},
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'from_warehouse', label: 'Source Warehouse', type: 'text' },
							{ name: 'to_warehouse', label: 'Target Warehouse', type: 'text' }
						]
					},
					{
						label: 'Items',
						fields: [
							{ name: 'item', label: 'Item', type: 'text', required: true },
							{ name: 'qty', label: 'Qty', type: 'number', required: true }
						]
					}
				]
			}
		},
		account: {
			label: 'Account',
			labelPlural: 'Chart of Accounts',
			columns: [
				{ field: 'number', label: 'Number', width: 100 },
				{ field: 'name', label: 'Account Name', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'rootType', label: 'Root Type' },
				{ field: 'balance', label: 'Balance', format: 'currency', align: 'right' }
			],
			filters: ['Asset', 'Liability', 'Equity', 'Income', 'Expense'],
			filterField: 'rootType',
			createForm: {
				action: 'add-account',
				submitLabel: 'Create Account',
				sections: [
					{
						label: 'Account Details',
						fields: [
							{ name: 'number', label: 'Account Number', type: 'text', required: true },
							{ name: 'name', label: 'Account Name', type: 'text', required: true },
							{
								name: 'root_type',
								label: 'Root Type',
								type: 'select',
								options: ['Asset', 'Liability', 'Equity', 'Income', 'Expense'],
								required: true
							},
							{ name: 'account_type', label: 'Account Type', type: 'text' },
							{ name: 'parent_account', label: 'Parent Account', type: 'text' }
						]
					}
				]
			}
		},
		journal_entry: {
			label: 'Journal Entry',
			labelPlural: 'Journal Entries',
			columns: [
				{ field: 'id', label: 'JE#', width: 120 },
				{ field: 'type', label: 'Type', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Total', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Cancelled'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981',
				Cancelled: '#ef4444'
			},
			createForm: {
				action: 'add-journal-entry',
				submitLabel: 'Create Journal Entry',
				sections: [
					{
						label: 'Entry Details',
						fields: [
							{
								name: 'type',
								label: 'Entry Type',
								type: 'select',
								options: ['Journal Entry', 'Opening Entry', 'Adjustment', 'Depreciation'],
								required: true
							},
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'reference', label: 'Reference', type: 'text' },
							{ name: 'remark', label: 'Remark', type: 'textarea' }
						]
					}
				]
			}
		},
		payment_entry: {
			label: 'Payment',
			labelPlural: 'Payments',
			columns: [
				{ field: 'id', label: 'PE#', width: 120 },
				{ field: 'party', label: 'Party', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'amount', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#10b981'
			},
			createForm: {
				action: 'add-payment',
				submitLabel: 'Create Payment',
				sections: [
					{
						label: 'Payment Details',
						fields: [
							{
								name: 'payment_type',
								label: 'Payment Type',
								type: 'select',
								options: ['Receive', 'Pay'],
								required: true
							},
							{ name: 'party', label: 'Party', type: 'text', required: true },
							{ name: 'date', label: 'Posting Date', type: 'date', required: true },
							{ name: 'amount', label: 'Amount', type: 'currency', required: true },
							{
								name: 'mode',
								label: 'Mode of Payment',
								type: 'select',
								options: ['Cash', 'Bank Transfer', 'Check', 'Credit Card']
							},
							{ name: 'reference', label: 'Reference No.', type: 'text' }
						]
					}
				]
			}
		},
		employee: {
			label: 'Employee',
			labelPlural: 'Employees',
			columns: [
				{ field: 'name', label: 'Name', primary: true },
				{ field: 'department', label: 'Department' },
				{ field: 'designation', label: 'Designation' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Active', 'Inactive', 'On Leave'],
			statusColors: {
				Active: '#10b981',
				Inactive: '#64748b',
				'On Leave': '#f59e0b'
			},
			createForm: {
				action: 'add-employee',
				submitLabel: 'Add Employee',
				sections: [
					{
						label: 'Employee Info',
						fields: [
							{ name: 'first_name', label: 'First Name', type: 'text', required: true },
							{ name: 'last_name', label: 'Last Name', type: 'text', required: true },
							{ name: 'email', label: 'Email', type: 'email', required: true },
							{ name: 'department', label: 'Department', type: 'text' },
							{ name: 'designation', label: 'Designation', type: 'text' },
							{ name: 'date_of_joining', label: 'Date of Joining', type: 'date', required: true }
						]
					}
				]
			}
		},
		expense_claim: {
			label: 'Expense Claim',
			labelPlural: 'Expense Claims',
			columns: [
				{ field: 'id', label: 'EC#', width: 120 },
				{ field: 'employee', label: 'Employee', primary: true },
				{ field: 'date', label: 'Date', format: 'date' },
				{ field: 'total', label: 'Amount', format: 'currency', align: 'right' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Draft', 'Submitted', 'Approved', 'Rejected'],
			statusColors: {
				Draft: '#64748b',
				Submitted: '#06b6d4',
				Approved: '#10b981',
				Rejected: '#ef4444'
			},
			createForm: {
				action: 'add-expense-claim',
				submitLabel: 'Submit Expense Claim',
				sections: [
					{
						label: 'Claim Details',
						fields: [
							{ name: 'employee', label: 'Employee', type: 'text', required: true },
							{ name: 'date', label: 'Expense Date', type: 'date', required: true },
							{
								name: 'expense_type',
								label: 'Expense Type',
								type: 'select',
								options: ['Travel', 'Meals', 'Office Supplies', 'Software', 'Other'],
								required: true
							},
							{ name: 'amount', label: 'Amount', type: 'currency', required: true },
							{ name: 'description', label: 'Description', type: 'textarea' }
						]
					}
				]
			}
		},
		company: {
			label: 'Company',
			labelPlural: 'Companies',
			columns: [
				{ field: 'name', label: 'Company Name', primary: true },
				{ field: 'currency', label: 'Currency' },
				{ field: 'country', label: 'Country' }
			],
			filters: [],
			createForm: {
				action: 'setup-company',
				submitLabel: 'Setup Company',
				sections: [
					{
						label: 'Company Details',
						fields: [
							{ name: 'name', label: 'Company Name', type: 'text', required: true },
							{ name: 'abbreviation', label: 'Abbreviation', type: 'text', required: true },
							{ name: 'currency', label: 'Default Currency', type: 'text', required: true },
							{ name: 'country', label: 'Country', type: 'text', required: true }
						]
					}
				]
			}
		},
		fiscal_year: {
			label: 'Fiscal Year',
			labelPlural: 'Fiscal Years',
			columns: [
				{ field: 'name', label: 'Fiscal Year', primary: true },
				{ field: 'start', label: 'Start', format: 'date' },
				{ field: 'end', label: 'End', format: 'date' },
				{ field: 'status', label: 'Status', format: 'status_badge' }
			],
			filters: ['Open', 'Closed'],
			statusColors: {
				Open: '#10b981',
				Closed: '#64748b'
			},
			createForm: {
				action: 'add-fiscal-year',
				submitLabel: 'Create Fiscal Year',
				sections: [
					{
						label: 'Period',
						fields: [
							{ name: 'name', label: 'Name', type: 'text', required: true },
							{ name: 'start_date', label: 'Start Date', type: 'date', required: true },
							{ name: 'end_date', label: 'End Date', type: 'date', required: true }
						]
					}
				]
			}
		},
		tax_template: {
			label: 'Tax Template',
			labelPlural: 'Tax Templates',
			columns: [
				{ field: 'name', label: 'Template Name', primary: true },
				{ field: 'type', label: 'Type' },
				{ field: 'rate', label: 'Rate' }
			],
			filters: [],
			createForm: {
				action: 'add-tax-template',
				submitLabel: 'Create Tax Template',
				sections: [
					{
						label: 'Template Details',
						fields: [
							{ name: 'name', label: 'Template Name', type: 'text', required: true },
							{
								name: 'template_type',
								label: 'Type',
								type: 'select',
								options: ['Sales', 'Purchase', 'Item'],
								required: true
							},
							{ name: 'rate', label: 'Tax Rate (%)', type: 'number', required: true }
						]
					}
				]
			}
		}
	},

	attention: [
		{
			message: '5 invoices overdue > 30 days ($12,400)',
			severity: 'warning',
			href: '/sales_invoice'
		},
		{
			message: '2 purchase receipts pending inspection',
			severity: 'warning',
			href: '/purchase_receipt'
		},
		{
			message: 'Bank reconciliation 15 days overdue',
			severity: 'critical',
			href: '/journal_entry'
		},
		{ message: '3 stock items below reorder level', severity: 'info', href: '/item' }
	],

	activity: [
		{
			message: 'Invoice INV-001 submitted to Acme Corp',
			timestamp: '2h ago',
			icon: '📄',
			href: '/sales_invoice'
		},
		{ message: 'Payment $1,200 received from Jane Smith', timestamp: '4h ago', icon: '💰' },
		{
			message: 'Customer TechStart Inc updated',
			timestamp: 'Yesterday',
			icon: '👤',
			href: '/customer'
		},
		{
			message: 'Quotation QT-042 sent to Global Trading',
			timestamp: 'Yesterday',
			icon: '📧'
		},
		{ message: 'Purchase Order PO-018 approved', timestamp: '2 days ago', icon: '✅' },
		{
			message: 'Delivery Note DN-012 submitted',
			timestamp: '2 days ago',
			icon: '📦',
			href: '/delivery_note'
		}
	],

	mockData: {
		customer: [
			{ name: 'Acme Corp', type: 'Company', territory: 'West', email: 'billing@acme.com', balance: 12400 },
			{ name: 'Jane Smith', type: 'Individual', territory: 'East', email: 'jane@email.com', balance: 3200 },
			{ name: 'TechStart Inc', type: 'Company', territory: 'West', email: 'ap@techstart.io', balance: 8900 },
			{ name: 'Bob Wilson', type: 'Individual', territory: 'Central', email: 'bob@wilson.net', balance: 1500 },
			{ name: 'Global Trading Co', type: 'Company', territory: 'East', email: 'finance@globaltrade.com', balance: 24100 },
			{ name: 'Sarah Chen', type: 'Individual', territory: 'West', email: 'sarah.chen@gmail.com', balance: 750 },
			{ name: 'Metro Services LLC', type: 'Company', territory: 'Central', email: 'accounts@metro.com', balance: 5600 }
		],
		quotation: [
			{ id: 'QT-041', customer: 'Acme Corp', date: '2026-03-08', total: 8500, validUntil: '2026-04-08', status: 'Submitted' },
			{ id: 'QT-042', customer: 'Global Trading Co', date: '2026-03-09', total: 22000, validUntil: '2026-04-09', status: 'Submitted' },
			{ id: 'QT-043', customer: 'Jane Smith', date: '2026-03-10', total: 1200, validUntil: '2026-04-10', status: 'Draft' },
			{ id: 'QT-044', customer: 'Metro Services LLC', date: '2026-03-10', total: 6800, validUntil: '2026-04-10', status: 'Draft' }
		],
		sales_order: [
			{ id: 'SO-031', customer: 'Acme Corp', date: '2026-03-05', total: 4800, deliveryDate: '2026-03-15', status: 'Submitted' },
			{ id: 'SO-032', customer: 'TechStart Inc', date: '2026-03-06', total: 12200, deliveryDate: '2026-03-16', status: 'Submitted' },
			{ id: 'SO-033', customer: 'Global Trading Co', date: '2026-03-07', total: 18500, deliveryDate: '2026-03-20', status: 'Delivered' },
			{ id: 'SO-034', customer: 'Bob Wilson', date: '2026-03-08', total: 2100, deliveryDate: '2026-03-18', status: 'Submitted' },
			{ id: 'SO-035', customer: 'Sarah Chen', date: '2026-03-09', total: 950, deliveryDate: '2026-03-19', status: 'Draft' }
		],
		delivery_note: [
			{ id: 'DN-011', customer: 'Global Trading Co', salesOrder: 'SO-033', date: '2026-03-09', status: 'Submitted' },
			{ id: 'DN-012', customer: 'Acme Corp', salesOrder: 'SO-031', date: '2026-03-10', status: 'Draft' }
		],
		sales_invoice: [
			{ id: 'INV-001', customer: 'Acme Corp', date: '2026-03-08', total: 4800, outstanding: 4800, status: 'Submitted' },
			{ id: 'INV-002', customer: 'Jane Smith', date: '2026-03-05', total: 1200, outstanding: 0, status: 'Paid' },
			{ id: 'INV-003', customer: 'TechStart Inc', date: '2026-02-15', total: 8900, outstanding: 8900, status: 'Overdue' },
			{ id: 'INV-004', customer: 'Global Trading Co', date: '2026-03-10', total: 15200, outstanding: 15200, status: 'Draft' },
			{ id: 'INV-005', customer: 'Bob Wilson', date: '2026-03-01', total: 3500, outstanding: 0, status: 'Paid' },
			{ id: 'INV-006', customer: 'Metro Services LLC', date: '2026-02-20', total: 5600, outstanding: 5600, status: 'Overdue' }
		],
		credit_note: [
			{ id: 'CN-001', customer: 'Jane Smith', invoice: 'INV-002', amount: 200, date: '2026-03-06', status: 'Submitted' }
		],
		supplier: [
			{ name: 'Steel Works Inc', type: 'Company', territory: 'West', balance: 18200 },
			{ name: 'Pacific Supplies', type: 'Company', territory: 'West', balance: 7400 },
			{ name: 'Mike Rivera', type: 'Individual', territory: 'Central', balance: 2100 },
			{ name: 'National Parts Co', type: 'Company', territory: 'East', balance: 11800 }
		],
		purchase_order: [
			{ id: 'PO-018', supplier: 'Steel Works Inc', date: '2026-03-08', total: 9400, status: 'Submitted' },
			{ id: 'PO-019', supplier: 'Pacific Supplies', date: '2026-03-09', total: 3200, status: 'Draft' },
			{ id: 'PO-020', supplier: 'National Parts Co', date: '2026-03-10', total: 6800, status: 'Received' }
		],
		purchase_receipt: [
			{ id: 'GRN-008', supplier: 'National Parts Co', purchaseOrder: 'PO-020', date: '2026-03-10', status: 'Submitted' },
			{ id: 'GRN-009', supplier: 'Steel Works Inc', purchaseOrder: 'PO-018', date: '2026-03-10', status: 'Draft' }
		],
		purchase_invoice: [
			{ id: 'BILL-014', supplier: 'National Parts Co', date: '2026-03-10', total: 6800, outstanding: 6800, status: 'Submitted' },
			{ id: 'BILL-015', supplier: 'Pacific Supplies', date: '2026-02-25', total: 4100, outstanding: 4100, status: 'Overdue' }
		],
		item: [
			{ name: 'Widget A', group: 'Finished Goods', uom: 'Nos', cost: 45, stock: 240 },
			{ name: 'Widget B', group: 'Finished Goods', uom: 'Nos', cost: 78, stock: 125 },
			{ name: 'Steel Rod (1m)', group: 'Raw Materials', uom: 'Nos', cost: 12, stock: 500 },
			{ name: 'Copper Wire (100ft)', group: 'Raw Materials', uom: 'Roll', cost: 34, stock: 80 },
			{ name: 'Packaging Box (Med)', group: 'Packing', uom: 'Nos', cost: 2, stock: 1200 }
		],
		warehouse: [
			{ name: 'Main Warehouse', type: 'Main', address: '123 Industrial Ave', items: 38 },
			{ name: 'Transit Storage', type: 'Transit', address: '456 Dock St', items: 5 },
			{ name: 'Returns/Scrap', type: 'Scrap', address: '123 Industrial Ave', items: 12 }
		],
		stock_entry: [
			{ id: 'SE-041', type: 'Material Receipt', date: '2026-03-10', from: '—', to: 'Main Warehouse', status: 'Submitted' },
			{ id: 'SE-042', type: 'Material Transfer', date: '2026-03-10', from: 'Main Warehouse', to: 'Transit Storage', status: 'Draft' }
		],
		account: [
			{ number: '1000', name: 'Cash', type: 'Cash', rootType: 'Asset', balance: 42800 },
			{ number: '1100', name: 'Accounts Receivable', type: 'Receivable', rootType: 'Asset', balance: 48200 },
			{ number: '1200', name: 'Inventory', type: 'Stock', rootType: 'Asset', balance: 67400 },
			{ number: '2000', name: 'Accounts Payable', type: 'Payable', rootType: 'Liability', balance: 39500 },
			{ number: '3000', name: 'Retained Earnings', type: 'Equity', rootType: 'Equity', balance: 125000 },
			{ number: '4000', name: 'Sales Revenue', type: 'Income', rootType: 'Income', balance: 142800 },
			{ number: '5000', name: 'Cost of Goods Sold', type: 'COGS', rootType: 'Expense', balance: 86400 }
		],
		journal_entry: [
			{ id: 'JE-088', type: 'Journal Entry', date: '2026-03-08', total: 4800, status: 'Submitted' },
			{ id: 'JE-089', type: 'Adjustment', date: '2026-03-09', total: 1200, status: 'Draft' },
			{ id: 'JE-090', type: 'Depreciation', date: '2026-03-10', total: 850, status: 'Submitted' }
		],
		payment_entry: [
			{ id: 'PE-055', party: 'Jane Smith', type: 'Receive', date: '2026-03-08', amount: 1200, status: 'Submitted' },
			{ id: 'PE-056', party: 'Bob Wilson', type: 'Receive', date: '2026-03-09', amount: 3500, status: 'Submitted' },
			{ id: 'PE-057', party: 'Steel Works Inc', type: 'Pay', date: '2026-03-10', amount: 9400, status: 'Draft' }
		],
		employee: [
			{ name: 'Alice Johnson', department: 'Sales', designation: 'Sales Manager', status: 'Active' },
			{ name: 'David Park', department: 'Accounting', designation: 'Accountant', status: 'Active' },
			{ name: 'Maria Santos', department: 'Warehouse', designation: 'Warehouse Lead', status: 'Active' },
			{ name: 'James Lee', department: 'Sales', designation: 'Sales Rep', status: 'On Leave' },
			{ name: 'Emily Davis', department: 'Admin', designation: 'HR Manager', status: 'Active' }
		],
		expense_claim: [
			{ id: 'EC-012', employee: 'Alice Johnson', date: '2026-03-08', total: 450, status: 'Approved' },
			{ id: 'EC-013', employee: 'James Lee', date: '2026-03-09', total: 820, status: 'Submitted' },
			{ id: 'EC-014', employee: 'David Park', date: '2026-03-10', total: 125, status: 'Draft' }
		],
		company: [{ name: 'ERPClaw Demo Inc', currency: 'USD', country: 'United States' }],
		fiscal_year: [
			{ name: 'FY 2025-26', start: '2025-04-01', end: '2026-03-31', status: 'Open' },
			{ name: 'FY 2024-25', start: '2024-04-01', end: '2025-03-31', status: 'Closed' }
		],
		tax_template: [
			{ name: 'US Sales Tax (8.25%)', type: 'Sales', rate: '8.25%' },
			{ name: 'US Sales Tax (0%)', type: 'Sales', rate: '0%' },
			{ name: 'Purchase Tax', type: 'Purchase', rate: '8.25%' }
		]
	}
};
