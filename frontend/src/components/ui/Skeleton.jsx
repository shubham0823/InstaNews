import React from 'react';
import { cn } from './Button';

export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn("animate-pulse rounded-2xl bg-gray-200 dark:bg-slate-800/80", className)}
      {...props}
    />
  );
}
