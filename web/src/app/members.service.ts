import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../environments/environment';
import type {
  MemberDetail,
  PaginatedMembers,
  RegisteredInterest,
} from './models';

@Injectable({ providedIn: 'root' })
export class MembersService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  listMembers(skip: number, take: number, q: string | null): Observable<PaginatedMembers> {
    let params = new HttpParams().set('skip', String(skip)).set('take', String(take));
    if (q && q.trim()) {
      params = params.set('q', q.trim());
    }
    return this.http.get<PaginatedMembers>(`${this.base}/api/members`, { params });
  }

  getMember(id: number): Observable<MemberDetail> {
    return this.http.get<MemberDetail>(`${this.base}/api/members/${id}`);
  }

  getInterests(memberId: number): Observable<RegisteredInterest[]> {
    return this.http.get<RegisteredInterest[]>(
      `${this.base}/api/members/${memberId}/interests`,
    );
  }
}
