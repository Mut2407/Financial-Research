import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Eye, EyeOff, Loader2 } from 'lucide-react';

const registerSchema = z.object({
  username: z.string().min(3, 'Tối thiểu 3 ký tự'),
  email: z.string().email('Email không hợp lệ'),
  password: z.string().min(6, 'Tối thiểu 6 ký tự'),
  confirmPassword: z.string(),
}).refine((d) => d.password === d.confirmPassword, {
  message: 'Mật khẩu xác nhận không khớp',
  path: ['confirmPassword'],
});
type RegisterForm = z.infer<typeof registerSchema>;

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const [showPwd, setShowPwd] = React.useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (_data: RegisterForm) => {
    await new Promise((r) => setTimeout(r, 600));
    navigate('/login');
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="fsd-logo text-3xl mb-2">FSD //</div>
        <p className="text-sm text-slate-500 font-medium">Data Lake Terminal</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-200/40 p-8">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-slate-900">Tạo tài khoản</h1>
          <p className="text-sm text-slate-500 mt-1">Điền thông tin để đăng ký hệ thống</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {[
            { name: 'username', label: 'Tên đăng nhập', type: 'text', placeholder: 'your_username' },
            { name: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
          ].map(({ name, label, type, placeholder }) => (
            <div key={name} className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{label}</label>
              <input
                type={type}
                {...register(name as any)}
                placeholder={placeholder}
                className="input-field"
              />
              {(errors as any)[name] && (
                <p className="text-xs text-red-500 mt-1">{(errors as any)[name].message}</p>
              )}
            </div>
          ))}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Mật khẩu</label>
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                {...register('password')}
                placeholder="••••••••"
                className="input-field pr-10"
              />
              <button type="button" onClick={() => setShowPwd((p) => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Xác nhận mật khẩu</label>
            <input type="password" {...register('confirmPassword')} placeholder="••••••••" className="input-field" />
            {errors.confirmPassword && <p className="text-xs text-red-500 mt-1">{errors.confirmPassword.message}</p>}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
            {isSubmitting ? (
              <><Loader2 size={14} className="animate-spin" /> Đang xử lý...</>
            ) : (
              <><UserPlus size={14} /> Đăng ký</>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-6">
          Đã có tài khoản?{' '}
          <Link to="/login" className="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition-colors">
            Đăng nhập
          </Link>
        </p>
      </div>
    </div>
  );
};
