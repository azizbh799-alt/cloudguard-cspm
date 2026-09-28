import { apiFetch } from "./client"
export const login = (email:string,password:string) => apiFetch<{access_token:string;user:{id:number;email:string;full_name:string}}>("/auth/login",{method:"POST",body:JSON.stringify({email,password})})
export const me = () => apiFetch("/auth/me")
