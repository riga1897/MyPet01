import { Sparkles, Flower2 } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-primary">
              <Flower2 className="size-7" />
              <Sparkles className="size-5" />
            </div>
            <div>
              <h1 className="text-xl">Гармония Души</h1>
              <p className="text-xs text-muted-foreground">Йога & Эфирные масла</p>
            </div>
          </div>
          
          <nav className="hidden md:flex items-center gap-6">
            <a href="#home" className="transition-colors hover:text-primary">
              Главная
            </a>
            <a href="#videos" className="transition-colors hover:text-primary">
              Видео
            </a>
            <a href="#about" className="transition-colors hover:text-primary">
              О блоге
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
