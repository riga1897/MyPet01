import { Sparkles } from "lucide-react";

export function Hero() {
  return (
    <section id="home" className="relative py-20 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto max-w-5xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/50 text-accent-foreground">
          <Sparkles className="size-4" />
          <span className="text-sm">Добро пожаловать в мир гармонии</span>
        </div>
        
        <h1 className="mb-6 text-4xl sm:text-5xl lg:text-6xl">
          Йога и Эфирные масла
          <br />
          <span className="text-primary">для вашей души</span>
        </h1>
        
        <p className="mx-auto max-w-2xl text-lg text-muted-foreground mb-8">
          Присоединяйтесь ко мне в путешествии к внутренней гармонии через практики йоги 
          и целительную силу натуральных эфирных масел.
        </p>
        
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="#videos"
            className="px-8 py-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Смотреть видео
          </a>
          <a
            href="#about"
            className="px-8 py-3 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/90 transition-colors"
          >
            Узнать больше
          </a>
        </div>
      </div>
      
      {/* Декоративные элементы */}
      <div className="absolute top-20 left-10 w-20 h-20 rounded-full bg-accent/20 blur-3xl" />
      <div className="absolute bottom-20 right-10 w-32 h-32 rounded-full bg-secondary/20 blur-3xl" />
    </section>
  );
}
