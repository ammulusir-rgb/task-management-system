import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import { EmailConfiguration, EmailRule, ProcessedEmail } from '@models/index';

export interface EmailConfigurationRequest {
  imap_enabled: boolean;
  imap_host: string;
  imap_port: number;
  imap_use_ssl: boolean;
  imap_username: string;
  imap_password?: string;
  smtp_enabled: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
  smtp_username: string;
  smtp_password?: string;
  task_email_address: string;
  default_project: string;
  auto_assign_reporter: boolean;
}

export interface EmailRuleRequest {
  name: string;
  rule_type: string;
  rule_value: string;
  is_active: boolean;
  target_project: string;
  default_assignee?: string;
  default_priority: string;
  default_status: string;
}

export interface ConnectionTestResult {
  imap: boolean;
  smtp: boolean;
  errors: string[];
}

@Injectable({
  providedIn: 'root',
})
export class EmailService {
  private http = inject(HttpClient);

  private get baseUrl(): string {
    return `${environment.apiUrl}/emails`;
  }

  // Email Configuration
  getConfiguration(): Observable<EmailConfiguration | null> {
    return this.http.get<EmailConfiguration>(`${this.baseUrl}/configurations/`);
  }

  createConfiguration(data: EmailConfigurationRequest): Observable<EmailConfiguration> {
    return this.http.post<EmailConfiguration>(`${this.baseUrl}/configurations/`, data);
  }

  updateConfiguration(id: string, data: Partial<EmailConfigurationRequest>): Observable<EmailConfiguration> {
    return this.http.patch<EmailConfiguration>(`${this.baseUrl}/configurations/${id}/`, data);
  }

  testConnection(configId: string): Observable<ConnectionTestResult> {
    return this.http.post<ConnectionTestResult>(`${this.baseUrl}/configurations/${configId}/test_connection/`, {});
  }

  processEmails(configId: string): Observable<{ message: string; task_id: string }> {
    return this.http.post<{ message: string; task_id: string }>(
      `${this.baseUrl}/configurations/${configId}/process_emails/`, 
      {}
    );
  }

  // Email Rules
  getRules(): Observable<EmailRule[]> {
    return this.http.get<EmailRule[]>(`${this.baseUrl}/rules/`);
  }

  createRule(data: EmailRuleRequest): Observable<EmailRule> {
    return this.http.post<EmailRule>(`${this.baseUrl}/rules/`, data);
  }

  updateRule(id: string, data: Partial<EmailRuleRequest>): Observable<EmailRule> {
    return this.http.patch<EmailRule>(`${this.baseUrl}/rules/${id}/`, data);
  }

  deleteRule(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/rules/${id}/`);
  }

  // Processed Emails
  getProcessedEmails(): Observable<ProcessedEmail[]> {
    return this.http.get<ProcessedEmail[]>(`${this.baseUrl}/processed/`);
  }
}