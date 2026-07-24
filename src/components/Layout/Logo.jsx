import { Link } from 'react-router-dom';

export default function Logo({ compact = false, className = '' }) {
  return (
    <Link
      to="/"
      className={`group inline-flex flex-col leading-none hover:opacity-90 transition-opacity ${className}`}
      aria-label="Agarwal Global Investments — Home"
    >
      <span className="font-serif text-[1.65rem] font-bold tracking-tight text-[#111111] italic">
        AGI
      </span>
      {!compact && (
        <>
          <span className="text-[10px] font-semibold tracking-[0.12em] uppercase text-[#333333] mt-0.5">
            Agarwal Global Investments
          </span>
          <span className="text-[9px] tracking-wide text-[#767676] mt-0.5 hidden sm:block">
            Independent Equity Research
          </span>
        </>
      )}
    </Link>
  );
}
