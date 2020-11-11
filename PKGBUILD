pkgname=gcc
pkgver=10.2.0
vcs=git
gittag=releases/gcc-${pkgver}
relmon_id=6502

build() {
    # do not run fixincludes
    sed -i 's@\./fixinc\.sh@-c true@' gcc/Makefile.in
    mkdir -v gcc-build
    cd gcc-build
    ../configure --prefix=/usr \
        --libdir=/usr/lib \
        --libexecdir=/usr/lib \
        --mandir=/usr/share/man \
        --infodir=/usr/share/info \
        --enable-languages=c,c++ \
        --disable-bootstrap \
        --disable-multilib \
        --build=x86_64-unknown-linux-gnu \
        --with-system-zlib \
        --with-zstd=no
    make
}

package() {
    cd gcc-build
    make DESTDIR=${pkgdir} install
    ln -sv ../bin/cpp ${pkgdir}/usr/lib
    ln -sv gcc ${pkgdir}/usr/bin/cc
    mv ${pkgdir}/usr/lib64/* ${pkgdir}/usr/lib/
    rmdir ${pkgdir}/usr/lib64
    mkdir -pv ${pkgdir}/usr/share/gdb/auto-load/usr/lib
    mv -v ${pkgdir}/usr/lib/*gdb.py ${pkgdir}/usr/share/gdb/auto-load/usr/lib
}
