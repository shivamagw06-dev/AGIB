import AskAgiFooter from '@/beta/components/AskAgiFooter';

export default function SurfaceChrome({ children, askPlaceholder }) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-20 pt-8 sm:px-6 lg:max-w-4xl">
      {children}
      <AskAgiFooter placeholder={askPlaceholder} />
    </div>
  );
}
