import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import type { MemberListItem, PaginatedMembers } from '../models';
import { MembersService } from '../members.service';

const PAGE_SIZE = 25;

@Component({
  selector: 'app-member-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './member-list.component.html',
  styleUrl: './member-list.component.css',
})
export class MemberListComponent implements OnInit {
  private readonly api = inject(MembersService);

  members: MemberListItem[] = [];
  total = 0;
  skip = 0;
  take = PAGE_SIZE;
  search = '';
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.api.listMembers(this.skip, this.take, this.search || null).subscribe({
      next: (res: PaginatedMembers) => {
        this.members = res.items;
        this.total = res.total;
        this.take = res.take;
        this.loading = false;
      },
      error: (err: unknown) => {
        this.loading = false;
        const msg =
          err instanceof HttpErrorResponse
            ? err.error?.detail || err.message
            : err instanceof Error
              ? err.message
              : String(err);
        this.error =
          msg || 'Could not load members. Is the API running on port 8000?';
      },
    });
  }

  doSearch(): void {
    this.skip = 0;
    this.load();
  }

  nextPage(): void {
    if (this.skip + this.take < this.total) {
      this.skip += this.take;
      this.load();
    }
  }

  prevPage(): void {
    if (this.skip >= this.take) {
      this.skip -= this.take;
      this.load();
    }
  }

  pageLabel(): string {
    if (this.total === 0) {
      return '0–0 of 0';
    }
    const from = this.skip + 1;
    const to = Math.min(this.skip + this.members.length, this.total);
    return `${from}–${to} of ${this.total}`;
  }
}
