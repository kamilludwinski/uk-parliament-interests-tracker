import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import type { MemberDetail, RegisteredInterest } from '../models';
import { MembersService } from '../members.service';

@Component({
  selector: 'app-member-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './member-detail.component.html',
  styleUrl: './member-detail.component.css',
})
export class MemberDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(MembersService);

  member: MemberDetail | null = null;
  interests: RegisteredInterest[] = [];
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isFinite(id)) {
      this.error = 'Invalid member id';
      this.loading = false;
      return;
    }

    forkJoin({
      member: this.api.getMember(id),
      interests: this.api.getInterests(id),
    }).subscribe({
      next: ({ member, interests }) => {
        this.member = member;
        this.interests = interests;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error =
          'Could not load member. Check API (port 8000) and that this id exists.';
      },
    });
  }

  /** Preserve API / table order of categories. */
  groupedSections(): { category: string; rows: RegisteredInterest[] }[] {
    const order: string[] = [];
    const map = new Map<string, RegisteredInterest[]>();
    for (const row of this.interests) {
      if (!map.has(row.category_name)) {
        order.push(row.category_name);
        map.set(row.category_name, []);
      }
      map.get(row.category_name)!.push(row);
    }
    return order.map((category) => ({
      category,
      rows: map.get(category)!,
    }));
  }
}
