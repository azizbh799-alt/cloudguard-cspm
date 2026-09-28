import { apiFetch } from "./client"
export type Dashboard = { security_score:number; critical:number; high:number; medium:number; low:number; total_findings:number; resources:number; last_scan:string|null; findings_by_severity:Record<string,number>; findings_by_service:Record<string,number> }
export const getDashboard = () => apiFetch<Dashboard>("/dashboard")
