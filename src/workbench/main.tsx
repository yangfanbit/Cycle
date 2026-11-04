import React from 'react';
import { createRoot } from 'react-dom/client';
import { Workbench } from './Workbench';
import './workbench.css';

const el = document.getElementById('root');
if (el) {
  createRoot(el).render(
    <React.StrictMode>
      <Workbench />
    </React.StrictMode>,
  );
}
