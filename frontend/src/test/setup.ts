import '@testing-library/jest-dom';
import { vi } from 'vitest';

HTMLDialogElement.prototype.showModal = vi.fn();
HTMLDialogElement.prototype.close = vi.fn();
