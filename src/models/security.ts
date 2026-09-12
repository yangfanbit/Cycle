/** Entity 7: Security —— 历史代表股票（V1 预留，可暂不使用） */
export interface Security {
  security_id: string;
  ticker: string;
  name: string;
  exchange: 'SH' | 'SZ' | 'BJ';
  sector?: string;
}

/** Entity 10: Observation —— 当前人工观察（不得直接修改 Rule） */
export interface Observation {
  observation_id: string;
  date: string; // ISO date
  theme_id: string;
  description: string;
  confidence: 'low' | 'medium' | 'high';
  source_id?: string;
}
