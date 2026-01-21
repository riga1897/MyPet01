import { Heart, Flower2 } from "lucide-react";

export function About() {
  return (
    <section id="about" className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="container mx-auto max-w-4xl">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 text-primary mb-4">
            <Flower2 className="size-8" />
          </div>
          <h2 className="text-3xl sm:text-4xl mb-4">О блоге</h2>
          <p className="text-muted-foreground">
            Место, где встречаются древние практики и природная мудрость
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div className="p-6 rounded-2xl bg-card border">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Heart className="size-6 text-primary" />
            </div>
            <h3 className="mb-3">Йога для всех</h3>
            <p className="text-muted-foreground">
              Практики йоги для начинающих и продвинутых. Асаны, дыхательные техники, 
              медитация — все для вашего физического и духовного развития.
            </p>
          </div>
          
          <div className="p-6 rounded-2xl bg-card border">
            <div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center mb-4">
              <Flower2 className="size-6 text-secondary" />
            </div>
            <h3 className="mb-3">Сила эфирных масел</h3>
            <p className="text-muted-foreground">
              Узнайте о целебных свойствах натуральных эфирных масел, способах их 
              применения и создания собственных ароматических композиций.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
