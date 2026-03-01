import { Component, inject, input, output, OnInit, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { OrganizationService } from '@core/services/organization.service';
import { TranslationService } from '@core/services/translation.service';
import { Organization } from '@models/index';
import { NavItem } from './sidebar.types';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
})
export class SidebarComponent implements OnInit {
  collapsed = input(false);
  toggleCollapse = output<void>();

  i18n = inject(TranslationService);
  private orgService = inject(OrganizationService);
  organizations = signal<Organization[]>([]);

  readonly navItems: NavItem[] = [
    { labelKey: 'sidebar.dashboard', icon: 'bi-house', route: '/dashboard' },
    { labelKey: 'sidebar.projects', icon: 'bi-folder', route: '/projects' },
    { labelKey: 'sidebar.myTasks', icon: 'bi-check2-square', route: '/tasks' },
    { labelKey: 'sidebar.notifications', icon: 'bi-bell', route: '/notifications' },
  ];

  ngOnInit(): void {
    this.orgService.list().subscribe({
      next: (res) => this.organizations.set(res.results),
    });
  }

  onOrgChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    console.log('Org changed to:', select.value);
  }
}
