import { ReactNode } from 'react';

type ModalProps = {
  open: boolean;
  onClose: () => void;
  children?: ReactNode;
};

const Modal = ({ open, onClose, children }: ModalProps) => {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-3xl bg-white p-6 shadow-xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-500 transition hover:bg-slate-200 hover:text-slate-700"
          aria-label="Close"
        >
          Close
        </button>
        <div className="min-h-[200px]">{children}</div>
      </div>
    </div>
  );
};

export default Modal;
