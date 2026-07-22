import { Link } from "react-router-dom";

export default function Logo() {
  return (
    <Link
      to="/"
      className="flex items-center gap-3 shrink-0"
    >
      {/* Replace with your logo image later */}
      <div className="w-11 h-11 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold">
        A
      </div>

      <div className="hidden sm:block leading-tight">
        <h1 className="text-lg font-semibold text-slate-900">
          Agarwal Global Investments
        </h1>

        <p className="text-xs text-slate-500">
          Independent Financial Research
        </p>
      </div>
    </Link>
  );
}