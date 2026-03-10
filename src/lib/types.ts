// ── KPI ──
export interface KPIItem {
	label: string;
	value: string;
	sub: string;
	color: string;
}

// ── Workflow ──
export interface WorkflowStep {
	label: string;
	count?: number;
	countColor?: string;
}

export interface WorkflowDef {
	key: string;
	label: string;
	icon: string;
	primaryAction: string;
	steps: WorkflowStep[];
}

// ── Sidebar ──
export interface SidebarItem {
	key: string;
	label: string;
	labelPlural: string;
}

export interface SidebarGroup {
	label: string;
	icon: string;
	items: SidebarItem[];
	expanded: boolean;
}

// ── DataTable ──
export interface ColumnDef {
	field: string;
	label: string;
	primary?: boolean;
	format?: 'currency' | 'date' | 'status_badge';
	align?: 'left' | 'right';
	width?: number;
}

// ── Form ──
export interface FormField {
	name: string;
	label: string;
	type: 'text' | 'email' | 'tel' | 'select' | 'textarea' | 'currency' | 'date' | 'number';
	required?: boolean;
	placeholder?: string;
	options?: string[];
}

export interface FormSection {
	label: string;
	fields: FormField[];
}

export interface FormSpec {
	action: string;
	sections: FormSection[];
	submitLabel: string;
}

// ── Entity ──
export interface EntityDef {
	label: string;
	labelPlural: string;
	columns: ColumnDef[];
	filters: string[];
	filterField?: string;
	createForm: FormSpec;
	statusColors?: Record<string, string>;
	detailSections?: { label: string; fields: string[]; collapsed?: boolean }[];
	actions?: string[];
}

// ── Attention ──
export interface AttentionItem {
	message: string;
	severity: 'critical' | 'warning' | 'info';
	href?: string;
}

// ── Activity ──
export interface ActivityItem {
	message: string;
	timestamp: string;
	icon?: string;
	href?: string;
}

// ── Search (CommandPalette) ──
export interface SearchResult {
	type: 'entity' | 'action' | 'page';
	label: string;
	description?: string;
	href: string;
	icon?: string;
}

// ── Chat ──
export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	href?: string;
	action?: { skill: string; action: string; params: Record<string, unknown> };
	suggestions?: string[];
}

// ── Vertical Layout ──
export interface VerticalLayout {
	name: string;
	label: string;
	description: string;
	icon: string;
	color: string;
	kpis: KPIItem[];
	workflows: WorkflowDef[];
	sidebar: SidebarGroup[];
	entities: Record<string, EntityDef>;
	mockData: Record<string, Record<string, unknown>[]>;
	attention: AttentionItem[];
	activity: ActivityItem[];
}
