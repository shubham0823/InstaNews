import React, { forwardRef } from 'react';
import { cn } from './Button';

export const Input = forwardRef(({ className, label, error, ...props }, ref) => {
  return (
    <div className="w-full space-y-1.5">
      {label && <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">{label}</label>}
      <input
        ref={ref}
        className={cn(
          "w-full px-4 py-3 rounded-xl border-0 bg-gray-100/80 dark:bg-gray-800/80 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-900 transition-all shadow-inner outline-none",
          error && "ring-2 ring-red-500 bg-red-50 dark:bg-red-900/10",
          className
        )}
        {...props}
      />
      {error && <p className="text-sm text-red-500 ml-1 animate-fade-in font-medium">{error}</p>}
    </div>
  );
});
Input.displayName = 'Input';
