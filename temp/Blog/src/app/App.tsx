import { Header } from "@/app/components/header";
import { Hero } from "@/app/components/hero";
import { VideoCard } from "@/app/components/video-card";
import { About } from "@/app/components/about";

const videos = [
  {
    id: 1,
    title: "Утренняя йога для пробуждения энергии",
    description: "20-минутный комплекс асан для бодрого начала дня. Подходит для всех уровней подготовки.",
    thumbnail: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx5b2dhJTIwbWVkaXRhdGlvbnxlbnwxfHx8fDE3Njg5NzgxODl8MA&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "20:15",
    date: "15 января 2026",
    category: "yoga" as const,
  },
  {
    id: 2,
    title: "Лавандовое масло: применение и свойства",
    description: "Все о лавандовом масле — от его успокаивающих свойств до практических способов использования в быту.",
    thumbnail: "https://images.unsplash.com/photo-1622976367831-cc206831cea3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlc3NlbnRpYWwlMjBvaWxzJTIwbGF2ZW5kZXJ8ZW58MXx8fHwxNzY4OTkyMjU0fDA&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "12:30",
    date: "12 января 2026",
    category: "oils" as const,
  },
  {
    id: 3,
    title: "Йога перед сном: расслабление и здоровый сон",
    description: "Мягкие асаны и дыхательные упражнения для глубокого расслабления и подготовки ко сну.",
    thumbnail: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx5b2dhJTIwbWVkaXRhdGlvbnxlbnwxfHx8fDE3Njg5NzgxODl8MA&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "15:45",
    date: "10 января 2026",
    category: "yoga" as const,
  },
  {
    id: 4,
    title: "Создание ароматической смеси для медитации",
    description: "Пошаговое руководство по созданию собственной смеси эфирных масел для практики медитации.",
    thumbnail: "https://images.unsplash.com/photo-1694166054675-f00812a2e687?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcm9tYXRoZXJhcHklMjBib3R0bGVzfGVufDF8fHx8MTc2ODk5MjI1NHww&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "18:20",
    date: "8 января 2026",
    category: "oils" as const,
  },
  {
    id: 5,
    title: "Пранаяма: дыхательные техники для начинающих",
    description: "Изучаем основные дыхательные практики йоги и их влияние на физическое и ментальное здоровье.",
    thumbnail: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx5b2dhJTIwbWVkaXRhdGlvbnxlbnwxfHx8fDE3Njg5NzgxODl8MA&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "22:10",
    date: "5 января 2026",
    category: "yoga" as const,
  },
  {
    id: 6,
    title: "Эфирные масла для укрепления иммунитета",
    description: "Какие эфирные масла помогут поддержать иммунную систему в холодное время года.",
    thumbnail: "https://images.unsplash.com/photo-1622976367831-cc206831cea3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlc3NlbnRpYWwlMjBvaWxzJTIwbGF2ZW5kZXJ8ZW58MXx8fHwxNzY4OTkyMjU0fDA&ixlib=rb-4.1.0&q=80&w=1080",
    duration: "14:55",
    date: "2 января 2026",
    category: "oils" as const,
  },
];

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      
      <main>
        <Hero />
        
        <section id="videos" className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="container mx-auto max-w-7xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl mb-4">Последние видео</h2>
              <p className="text-muted-foreground">
                Новые практики и советы каждую неделю
              </p>
            </div>
            
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
              {videos.map((video) => (
                <VideoCard key={video.id} {...video} />
              ))}
            </div>
          </div>
        </section>
        
        <About />
      </main>
      
      <footer className="py-8 px-4 border-t bg-muted/30">
        <div className="container mx-auto max-w-7xl text-center text-muted-foreground">
          <p>© 2026 Гармония Души. Блог о йоге и эфирных маслах.</p>
        </div>
      </footer>
    </div>
  );
}
