import { Play } from "lucide-react";
import { ImageWithFallback } from "@/app/components/figma/ImageWithFallback";

interface VideoCardProps {
  title: string;
  description: string;
  thumbnail: string;
  duration: string;
  date: string;
  category: "yoga" | "oils";
}

export function VideoCard({
  title,
  description,
  thumbnail,
  duration,
  date,
  category,
}: VideoCardProps) {
  return (
    <article className="group overflow-hidden rounded-2xl bg-card border transition-all hover:shadow-lg hover:-translate-y-1">
      <div className="relative aspect-video overflow-hidden bg-muted">
        <ImageWithFallback
          src={thumbnail}
          alt={title}
          className="size-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <div className="rounded-full bg-primary/90 p-4 backdrop-blur-sm">
            <Play className="size-6 text-white fill-white" />
          </div>
        </div>
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm rounded text-xs text-white">
          {duration}
        </div>
      </div>
      
      <div className="p-5">
        <div className="mb-2">
          <span
            className={`inline-block px-3 py-1 rounded-full text-xs ${
              category === "yoga"
                ? "bg-primary/10 text-primary"
                : "bg-secondary/10 text-secondary"
            }`}
          >
            {category === "yoga" ? "Йога" : "Эфирные масла"}
          </span>
        </div>
        
        <h3 className="mb-2 line-clamp-2 group-hover:text-primary transition-colors">
          {title}
        </h3>
        
        <p className="text-muted-foreground line-clamp-2 mb-3">
          {description}
        </p>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{date}</span>
        </div>
      </div>
    </article>
  );
}
